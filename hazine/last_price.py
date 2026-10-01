# -*- coding: utf-8 -*-
"""
محاسبه قیمت نهایی محصول — نرم‌افزار سپیدار
- محاسبه بازگشتی (اگر ماده اولیه خودش فرمول داشته باشد)
- انتخاب منبع قیمت (آخرین خرید / آخرین رسید)
- نمایش صحیح فارسی در ترمینال
"""

import sys
import socket
import logging
from datetime import datetime

import pyodbc
import arabic_reshaper
from bidi.algorithm import get_display

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


# ============================================================
# 🔤 اصلاح متن فارسی
# ============================================================
def fa(text):
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    try:
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def fp(text=""):
    print(fa(text))


def separator(char="=", n=90):
    print(char * n)


# ============================================================
# ⚙️ تنظیمات سراسری — منبع قیمت
# ============================================================
class PriceConfig:
    # 'last_purchase' یا 'last_receipt'
    SOURCE = 'last_receipt'

    @classmethod
    def source_label(cls):
        return {
            'last_purchase': 'آخرین خرید',
            'last_receipt': 'آخرین رسید',
        }.get(cls.SOURCE, cls.SOURCE)


# ============================================================
# 📝 Tee — ذخیره در فایل
# ============================================================
class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            try:
                s.write(data)
            except Exception:
                pass

    def flush(self):
        for s in self.streams:
            try:
                s.flush()
            except Exception:
                pass


# ============================================================
# 🔌 اتصال
# ============================================================
class DatabaseConnection:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            pc_name = socket.gethostname()
            self._server = pc_name if 'DESKTOP' in pc_name else "DESKTOP-OCIN559"
            self._database = "Sepidar01"
            self._driver = "{ODBC Driver 17 for SQL Server}"
            self._connection_string = (
                f"DRIVER={self._driver};"
                f"SERVER={self._server};"
                f"DATABASE={self._database};"
                f"Trusted_Connection=yes;"
            )

    def connect(self):
        if self._connection is None:
            self._connection = pyodbc.connect(self._connection_string)
            cur = self._connection.cursor()
            cur.execute("SET DATEFORMAT YMD")
            cur.close()
        return self._connection

    def get_connection(self):
        if self._connection is None:
            self.connect()
        return self._connection

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None


# ============================================================
# 🔍 جستجوی فرمول
# ============================================================
def find_formula(conn, product_name):
    query = """
    SELECT TOP 10
        pf.ProductFormulaID,
        pf.Code,
        pf.Title,
        pf.ItemRef,
        pf.ItemCode,
        pf.ItemTitle,
        pf.ItemUnitTitle,
        pf.Quantity,
        pf.EstimatedLabour,
        pf.EstimatedOverhead
    FROM [Sepidar01].[WKO].[vwProductFormula] pf
    WHERE pf.Title LIKE ? OR pf.ItemTitle LIKE ?
    ORDER BY pf.ProductFormulaID DESC
    """
    like = f"%{product_name}%"
    cursor = conn.cursor()
    cursor.execute(query, (like, like))
    cols = [c[0] for c in cursor.description]
    rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    cursor.close()
    return rows


def find_formula_by_item_ref(conn, item_ref):
    """
    آیا این آیتم خودش فرمول تولید داره؟
    اگه بله، برگردون (formula_id, formula_title, formula_qty)
    """
    query = """
    SELECT TOP 1
        pf.ProductFormulaID,
        pf.Code,
        pf.Title,
        pf.Quantity,
        pf.EstimatedLabour,
        pf.EstimatedOverhead
    FROM [Sepidar01].[WKO].[vwProductFormula] pf
    WHERE pf.ItemRef = ? AND pf.IsActive = 1
    ORDER BY pf.ProductFormulaID DESC
    """
    cursor = conn.cursor()
    cursor.execute(query, (item_ref,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return {
            'ProductFormulaID': row[0],
            'Code': row[1],
            'Title': row[2],
            'Quantity': float(row[3]) if row[3] else 1.0,
            'EstimatedLabour': float(row[4]) if row[4] else 0.0,
            'EstimatedOverhead': float(row[5]) if row[5] else 0.0,
        }
    return None


# ============================================================
# 📋 مواد اولیه فرمول
# ============================================================
def get_bom_items(conn, formula_id):
    query = """
    SELECT 
        fbi.FormulaBomItemID,
        fbi.ItemRef,
        i.Code AS ItemCode,
        i.Title AS ItemTitle,
        fbi.Quantity,
        u.Title AS UnitTitle
    FROM [Sepidar01].[WKO].[FormulaBomItem] fbi
    LEFT JOIN [Sepidar01].[INV].[Item] i ON fbi.ItemRef = i.ItemID
    LEFT JOIN [Sepidar01].[INV].[Unit] u ON i.UnitRef = u.UnitID
    WHERE fbi.ProductFormulaRef = ?
    ORDER BY fbi.FormulaBomItemID
    """
    cursor = conn.cursor()
    cursor.execute(query, (formula_id,))
    cols = [c[0] for c in cursor.description]
    rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    cursor.close()
    return rows


# ============================================================
# 💰 قیمت یک آیتم (بر اساس تنظیمات سراسری)
# ============================================================
def get_item_price_last_purchase(conn, item_ref):
    """آخرین قیمت خرید"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT TOP 1
                ipi.Price, ipi.NetPrice,
                inv.Number, inv.Date
            FROM [Sepidar01].[INV].[InventoryPurchaseInvoiceItem] ipi
            INNER JOIN [Sepidar01].[INV].[InventoryPurchaseInvoice] inv 
                ON ipi.InventoryPurchaseInvoiceRef = inv.InventoryPurchaseInvoiceID
            WHERE ipi.ItemRef = ?
            ORDER BY inv.Date DESC, ipi.InventoryPurchaseInvoiceItemID DESC
        """, (item_ref,))
        row = cursor.fetchone()
        if row and row[0] is not None:
            cursor.close()
            return {
                'price': float(row[0]),
                'net_price': float(row[1]) if row[1] else None,
                'source': 'آخرین خرید',
                'doc': f"فاکتور خرید {row[2]}",
                'date': row[3]
            }
    except Exception as e:
        logger.debug(f"last_purchase failed: {e}")
    cursor.close()
    return None


def get_item_price_last_receipt(conn, item_ref):
    """آخرین قیمت رسید انبار"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT TOP 1
                iri.Price, iri.NetPrice,
                inv.Number, inv.Date
            FROM [Sepidar01].[INV].[InventoryReceiptItem] iri
            INNER JOIN [Sepidar01].[INV].[InventoryReceipt] inv 
                ON iri.InventoryReceiptRef = inv.InventoryReceiptID
            WHERE iri.ItemRef = ?
            ORDER BY inv.Date DESC, iri.InventoryReceiptItemID DESC
        """, (item_ref,))
        row = cursor.fetchone()
        if row and row[0] is not None:
            cursor.close()
            return {
                'price': float(row[0]),
                'net_price': float(row[1]) if row[1] else None,
                'source': 'آخرین رسید',
                'doc': f"رسید {row[2]}",
                'date': row[3]
            }
    except Exception as e:
        logger.debug(f"last_receipt failed: {e}")
    cursor.close()
    return None


def get_item_price_raw(conn, item_ref):
    """قیمت خام بر اساس تنظیمات انتخاب‌شده کاربر"""
    if PriceConfig.SOURCE == 'last_purchase':
        return get_item_price_last_purchase(conn, item_ref)
    else:
        return get_item_price_last_receipt(conn, item_ref)


def get_item_price(conn, item_ref):
    """قیمت تک‌آیتم (بدون بازگشت) — با fallback"""
    # اولویت اول: منبع انتخاب‌شده
    p = get_item_price_raw(conn, item_ref)
    if p:
        return p

    # fallback: منبع دیگر
    if PriceConfig.SOURCE == 'last_purchase':
        p = get_item_price_last_receipt(conn, item_ref)
    else:
        p = get_item_price_last_purchase(conn, item_ref)
    if p:
        return p

    # fallback: قیمت تولیدی
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT TOP 1 Price
            FROM [Sepidar01].[INV].[ProducedItemPrice]
            WHERE ItemRef = ?
            ORDER BY ProducedItemPriceID DESC
        """, (item_ref,))
        row = cursor.fetchone()
        if row and row[0] is not None:
            cursor.close()
            return {
                'price': float(row[0]),
                'net_price': float(row[0]),
                'source': 'قیمت تولیدی',
                'doc': '-',
                'date': None
            }
    except Exception as e:
        logger.debug(f"produced_price failed: {e}")
    cursor.close()
    return None


# ============================================================
# 🧮 محاسبه بازگشتی قیمت یک آیتم
# ============================================================
def calculate_item_cost(
    conn,
    item_ref,
    quantity=1,
    depth=0,
    max_depth=10,
    visited=None,
    trace=True
):
    """
    قیمت یک آیتم رو حساب می‌کنه.
    - اگر خودش فرمول داشته باشه → بازگشتی فرمولش رو حساب کن
    - وگرنه → از منبع انتخاب‌شده قیمت بگیر

    برمی‌گردونه: (total_cost, details_dict)
    """
    indent = "   " * depth
    if visited is None:
        visited = set()

    # محافظت از حلقه بی‌پایان
    if item_ref in visited:
        if trace:
            fp(f"{indent}  ⚠️ حلقه تشخیص داده شد برای ItemRef={item_ref}")
        return 0.0, {'source': 'حلقه', 'items': []}

    if depth > max_depth:
        if trace:
            fp(f"{indent}  ⚠️ عمق بیش از حد مجاز")
        return 0.0, {'source': 'عمق زیاد', 'items': []}

    visited.add(item_ref)

    # ---- آیا این آیتم خودش فرمول داره؟ ----
    formula = find_formula_by_item_ref(conn, item_ref)

    if formula:
        if trace:
            fp(f"{indent}  🔧 خودش فرمول دارد → کد {formula['Code']} "
               f"({formula['Title']}) — مقدار فرمول: {formula['Quantity']}")

        # مواد اولیه این فرمول
        bom = get_bom_items(conn, formula['ProductFormulaID'])
        formula_qty = formula['Quantity'] if formula['Quantity'] else 1.0

        # ضریب تبدیل: چقدر از این فرمول لازم داریم؟
        ratio = quantity / formula_qty

        if trace:
            fp(f"{indent}     ضریب: {ratio:.6f} (نیاز {quantity} / فرمول {formula_qty})")

        total_sub = 0.0
        sub_items = []

        for sub in bom:
            sub_ref = sub['ItemRef']
            sub_qty_per_formula = float(sub['Quantity'])
            sub_qty_needed = sub_qty_per_formula * ratio

            sub_cost, sub_detail = calculate_item_cost(
                conn=conn,
                item_ref=sub_ref,
                quantity=sub_qty_needed,
                depth=depth + 1,
                max_depth=max_depth,
                visited=visited.copy(),
                trace=trace
            )

            total_sub += sub_cost
            sub_items.append({
                'item_ref': sub_ref,
                'item_code': sub['ItemCode'],
                'item_title': sub['ItemTitle'],
                'quantity': sub_qty_needed,
                'cost': sub_cost,
                'source': sub_detail.get('source'),
            })

            if trace:
                name = (sub['ItemTitle'] or '-')[:26]
                fp(f"{indent}     • {name:<28} "
                   f"{sub_qty_needed:>10.4f}  "
                   f"{sub_cost:>15,.0f} ریال "
                   f"[{sub_detail.get('source')}]")

        # دستمزد و سربار این فرمول (به نسبت)
        labour = formula['EstimatedLabour'] * ratio
        overhead = formula['EstimatedOverhead'] * ratio
        total = total_sub + labour + overhead

        if trace and (labour or overhead):
            fp(f"{indent}     + دستمزد: {labour:,.0f}  سربار: {overhead:,.0f}")

        if trace:
            fp(f"{indent}     ➡️ جمع فرمول: {total:,.0f} ریال")

        return total, {
            'source': f"فرمول {formula['Code']}",
            'formula_id': formula['ProductFormulaID'],
            'formula_title': formula['Title'],
            'items': sub_items,
            'material_cost': total_sub,
            'labour': labour,
            'overhead': overhead,
        }

    # ---- آیتم ساده: از قیمت خرید/رسید استفاده کن ----
    price_info = get_item_price(conn, item_ref)
    if not price_info:
        if trace:
            fp(f"{indent}  ⚠️ قیمت پیدا نشد")
        return 0.0, {'source': 'پیدا نشد', 'items': []}

    total = price_info['price'] * quantity
    return total, {
        'source': price_info['source'],
        'unit_price': price_info['price'],
        'items': []
    }


# ============================================================
# 🎯 محاسبه قیمت نهایی محصول
# ============================================================
def calculate_product_price(conn, product_name, quantity=1, verbose=True):
    if verbose:
        print()
        separator("=")
        fp(f"🔍 جستجوی محصول: {product_name}")
        separator("=")

    formulas = find_formula(conn, product_name)
    if not formulas:
        fp(f"❌ هیچ فرمولی برای «{product_name}» پیدا نشد.")
        return None

    if len(formulas) > 1:
        fp(f"\n📋 {len(formulas)} فرمول پیدا شد:")
        print()
        for idx, f in enumerate(formulas, 1):
            fp(f"  [{idx}] کد {f['Code']} — {f['Title']} "
               f"(محصول: {f['ItemTitle']})")
        print()
        choice = input(fa("شماره فرمول مورد نظر: ")).strip()
        try:
            formula = formulas[int(choice) - 1]
        except (ValueError, IndexError):
            fp("❌ انتخاب نامعتبر")
            return None
    else:
        formula = formulas[0]

    print()
    fp(f"✅ فرمول: کد {formula['Code']} — {formula['Title']}")
    fp(f"   محصول: {formula['ItemTitle']} ({formula['ItemCode']})")
    fp(f"   واحد:  {formula['ItemUnitTitle']}")
    fp(f"   مقدار: {formula['Quantity']}")
    fp(f"   منبع قیمت: {PriceConfig.source_label()}")

    bom = get_bom_items(conn, formula['ProductFormulaID'])
    if not bom:
        fp("⚠️ این فرمول ماده اولیه ندارد.")
        return None

    # ---- مواد اولیه با محاسبه بازگشتی ----
    print()
    fp(f"📦 محاسبه مواد اولیه ({len(bom)} قلم) — با احتساب فرمول‌های تودرتو")
    separator("=")

    formula_qty = float(formula['Quantity']) if formula['Quantity'] else 1.0
    ratio = quantity / formula_qty

    total_material_cost = 0.0
    missing = []
    rows_for_table = []

    for idx, item in enumerate(bom, 1):
        sub_qty = float(item['Quantity']) * ratio
        name = (item['ItemTitle'] or '-')[:28]

        fp(f"\n[{idx}] {name}  —  مقدار لازم: {sub_qty:.4f}")

        cost, detail = calculate_item_cost(
            conn=conn,
            item_ref=item['ItemRef'],
            quantity=sub_qty,
            depth=0,
            trace=True
        )

        if detail.get('source') == 'پیدا نشد':
            missing.append(item)

        total_material_cost += cost
        rows_for_table.append({
            'idx': idx,
            'name': name,
            'qty': sub_qty,
            'cost': cost,
            'source': detail.get('source'),
        })

    # ---- جدول خلاصه ----
    print()
    separator("=")
    fp("📊 خلاصه مواد اولیه")
    separator("=")
    fp(f"{'#':<4} {'نام':<28} {'مقدار':>12} {'هزینه':>18} {'منبع':<20}")
    separator("-", 90)

    for r in rows_for_table:
        line = (f"{r['idx']:<4} {r['name']:<28} "
                f"{r['qty']:>12.4f} {r['cost']:>18,.0f} "
                f"{str(r['source'])[:18]:<20}")
        fp(line)

    # ---- دستمزد و سربار ----
    labour = float(formula['EstimatedLabour'] or 0) * ratio
    overhead = float(formula['EstimatedOverhead'] or 0) * ratio
    total_cost = total_material_cost + labour + overhead

    # ---- جمع‌بندی ----
    print()
    separator("=")
    fp("🧮 محاسبه نهایی")
    separator("=")
    fp(f"  💵 جمع مواد اولیه : {total_material_cost:>18,.0f} ریال")
    fp(f"  👷 دستمزد        : {labour:>18,.0f} ریال")
    fp(f"  🏭 سربار         : {overhead:>18,.0f} ریال")
    print("  " + "-" * 62)
    fp(f"  🎯 قیمت تمام‌شده  : {total_cost:>18,.0f} ریال")
    if quantity > 0:
        fp(f"  📦 قیمت هر واحد   : {total_cost / quantity:>18,.0f} ریال")

    if missing:
        print()
        fp(f"⚠️ {len(missing)} ماده قیمت نداشتند:")
        for m in missing:
            fp(f"     • {m['ItemCode']} - {m['ItemTitle']}")

    # ---- مقایسه با قیمت فروش ----
    print()
    separator("=")
    fp("📊 مقایسه با قیمت فروش محصول نهایی")
    separator("=")

    final_price = get_item_price(conn, formula['ItemRef'])
    if final_price:
        fp(f"  💰 قیمت فروش فعلی : {final_price['price']:>18,.0f} ریال "
           f"({final_price['source']})")
        if total_cost > 0 and final_price['price'] > 0:
            profit = final_price['price'] - total_cost
            margin = (profit / final_price['price']) * 100
            fp(f"  📈 سود            : {profit:>18,.0f} ریال")
            fp(f"  📊 حاشیه سود      : {margin:>17.2f}%")
    else:
        fp("  ⚠️ قیمت فروش ثبت نشده.")

    return {
        'formula': formula,
        'material_cost': total_material_cost,
        'labour': labour,
        'overhead': overhead,
        'total': total_cost,
        'final_sale': final_price['price'] if final_price else None,
    }


# ============================================================
# ❓ پرسیدن منبع قیمت
# ============================================================
def ask_price_source():
    print()
    separator("=")
    fp("  ⚙️ انتخاب منبع قیمت مواد اولیه")
    separator("=")
    fp("  [1] آخرین خرید  (فاکتور خرید)")
    fp("  [2] آخرین رسید  (رسید انبار)")
    print()

    choice = input(fa("منبع قیمت (پیش‌فرض 2): ")).strip()

    if choice == "1":
        PriceConfig.SOURCE = 'last_purchase'
    else:
        PriceConfig.SOURCE = 'last_receipt'

    print()
    fp(f"✅ منبع قیمت انتخاب‌شده: {PriceConfig.source_label()}")


# ============================================================
# 🚀 Main
# ============================================================
def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"price_report_{ts}.txt"

    with open(log_file, "w", encoding="utf-8") as f:
        original_stdout = sys.stdout
        sys.stdout = Tee(original_stdout, f)

        try:
            db = DatabaseConnection()
            db.connect()
            conn = db.get_connection()

            try:
                # ---- انتخاب منبع قیمت ----
                ask_price_source()

                while True:
                    print()
                    separator("=")
                    fp("  💼 محاسبه قیمت محصول — نرم‌افزار سپیدار")
                    fp(f"  منبع قیمت: {PriceConfig.source_label()}")
                    separator("=")

                    name = input(fa("نام محصول (یا 'exit' / 'source' برای تغییر منبع): ")).strip()

                    if not name:
                        continue

                    if name.lower() == 'exit':
                        break

                    if name.lower() == 'source':
                        ask_price_source()
                        continue

                    try:
                        qty_input = input(fa("تعداد (پیش‌فرض 1): ")).strip()
                        qty = float(qty_input) if qty_input else 1
                    except ValueError:
                        qty = 1

                    try:
                        calculate_product_price(conn, name, qty)
                    except Exception as e:
                        fp(f"❌ خطا: {e}")
                        import traceback
                        traceback.print_exc()

            finally:
                db.close()

        finally:
            sys.stdout = original_stdout

    print()
    fp(f"🎉 خروجی در فایل ذخیره شد: {log_file}")


if __name__ == "__main__":
    main()