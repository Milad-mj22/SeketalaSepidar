# SepidarApp/activity_helper.py
"""
خواندن تاریخچه فعالیت کاربران از سپیدار
- از فیلد Creator در جداول استفاده می‌کند
- با FMK.User جوین می‌شود تا نام کاربر را بگیرد
"""
import logging
from SepidarApp.databaseConnector import db
from datetime import datetime

logger = logging.getLogger(__name__)


def get_users_map():
    """
    دریافت دیکشنری UserID → نام کاربر
    """
    users_map = {}
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                u.UserID,
                u.UserName,
                u.Name
            FROM [Sepidar01].[FMK].[User] u
        """)
        for row in cursor.fetchall():
            user_id = int(row[0])
            first_name = row[2] or ''
            last_name =  ''
            full_name = f"{first_name} {last_name}".strip()
            users_map[user_id] = {
                'user_id': user_id,
                'username': row[1] or '',
                'full_name': full_name or (row[1] or f'کاربر {user_id}'),
            }
    except Exception as e:
        logger.error(f"Error in get_users_map: {e}", exc_info=True)
    return users_map


def get_product_orders(date_from=None, date_to=None, creator=None):
    """
    دریافت سفارشات تولید از سپیدار
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        conditions = ["1=1"]
        params = []

        if date_from:
            conditions.append("CAST(po.Date AS DATE) >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("CAST(po.Date AS DATE) <= ?")
            params.append(date_to)
        if creator:
            conditions.append("po.Creator = ?")
            params.append(creator)

        where = " AND ".join(conditions)

        query = f"""
            SELECT 
                po.ProductOrderID,
                po.Number,
                po.Date,
                po.Creator,
                po.Quantity,
                po.ProductFormulaRef,
                pf.Code AS FormulaCode,
                pf.Title AS FormulaTitle,
                p.Code AS ProductCode,
                p.Title AS ProductTitle
            FROM [Sepidar01].[WKO].[ProductOrder] po
            LEFT JOIN [Sepidar01].[WKO].[ProductFormula] pf 
                ON po.ProductFormulaRef = pf.ProductFormulaID
            LEFT JOIN [Sepidar01].[INV].[Item] p 
                ON po.ProductRef = p.ItemID
            WHERE {where}
            ORDER BY po.Date DESC, po.ProductOrderID DESC
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                'id': int(row[0]),
                'number': int(row[1]) if row[1] else None,
                'date': row[2],
                'creator': int(row[3]) if row[3] else None,
                'quantity': float(row[4]) if row[4] else 0,
                'formula_ref': int(row[5]) if row[5] else None,
                'formula_code': row[6] or '',
                'formula_title': row[7] or '',
                'product_code': row[8] or '',
                'product_title': row[9] or '',
                'activity_type': 'product_order',
            })
        return result

    except Exception as e:
        logger.error(f"Error in get_product_orders: {e}", exc_info=True)
        return []


def get_inventory_deliveries(date_from=None, date_to=None, creator=None):
    """
    دریافت رسیدهای خروج انبار
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        conditions = ["1=1"]
        params = []

        if date_from:
            conditions.append("CAST(d.Date AS DATE) >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("CAST(d.Date AS DATE) <= ?")
            params.append(date_to)
        if creator:
            conditions.append("d.Creator = ?")
            params.append(creator)

        where = " AND ".join(conditions)

        query = f"""
            SELECT 
                d.InventoryDeliveryID,
                d.Number,
                d.Date,
                d.Creator,
                d.StockRef,
                d.TotalPrice,
                s.Title AS StockName,
                (SELECT COUNT(*) FROM [Sepidar01].[INV].[InventoryDeliveryItem] WHERE InventoryDeliveryRef = d.InventoryDeliveryID) AS ItemsCount
            FROM [Sepidar01].[INV].[InventoryDelivery] d
            LEFT JOIN [Sepidar01].[INV].[Stock] s ON d.StockRef = s.StockID
            WHERE {where}
            ORDER BY d.Date DESC, d.InventoryDeliveryID DESC
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                'id': int(row[0]),
                'number': int(row[1]) if row[1] else None,
                'date': row[2],
                'creator': int(row[3]) if row[3] else None,
                'stock_ref': int(row[4]) if row[4] else None,
                'total_price': float(row[5]) if row[5] else 0,
                'stock_name': row[6] or '',
                'items_count': int(row[7]) if row[7] else 0,
                'activity_type': 'inventory_delivery',
            })
        return result

    except Exception as e:
        logger.error(f"Error in get_inventory_deliveries: {e}", exc_info=True)
        return []


def get_inventory_receipts(date_from=None, date_to=None, creator=None):
    """
    دریافت رسیدهای ورود انبار
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        conditions = ["1=1"]
        params = []

        if date_from:
            conditions.append("CAST(r.Date AS DATE) >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("CAST(r.Date AS DATE) <= ?")
            params.append(date_to)
        if creator:
            conditions.append("r.Creator = ?")
            params.append(creator)

        where = " AND ".join(conditions)

        query = f"""
            SELECT 
                r.InventoryReceiptID,
                r.Number,
                r.Date,
                r.Creator,
                r.StockRef,
                r.TotalPrice,
                s.Title AS StockName,
                (SELECT COUNT(*) FROM [Sepidar01].[INV].[InventoryReceiptItem] WHERE InventoryReceiptRef = r.InventoryReceiptID) AS ItemsCount
            FROM [Sepidar01].[INV].[InventoryReceipt] r
            LEFT JOIN [Sepidar01].[INV].[Stock] s ON r.StockRef = s.StockID
            WHERE {where}
            ORDER BY r.Date DESC, r.InventoryReceiptID DESC
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                'id': int(row[0]),
                'number': int(row[1]) if row[1] else None,
                'date': row[2],
                'creator': int(row[3]) if row[3] else None,
                'stock_ref': int(row[4]) if row[4] else None,
                'total_price': float(row[5]) if row[5] else 0,
                'stock_name': row[6] or '',
                'items_count': int(row[7]) if row[7] else 0,
                'activity_type': 'inventory_receipt',
            })
        return result

    except Exception as e:
        logger.error(f"Error in get_inventory_receipts: {e}", exc_info=True)
        return []


def get_all_activities(date_from=None, date_to=None, creator=None):
    """
    ترکیب همه فعالیت‌ها در یک لیست
    """
    activities = []

    # 1. سفارشات تولید
    orders = get_product_orders(date_from, date_to, creator)
    activities.extend(orders)

    # 2. رسیدهای خروج
    deliveries = get_inventory_deliveries(date_from, date_to, creator)
    activities.extend(deliveries)

    # 3. رسیدهای ورود
    receipts = get_inventory_receipts(date_from, date_to, creator)
    activities.extend(receipts)

    # 4. ✅ اسناد حسابداری
    activities.extend(get_accounting_vouchers(date_from, date_to, creator))



    # مرتب‌سازی: جدیدترین اول
    activities.sort(key=lambda x: x['date'] if x['date'] else datetime.min, reverse=True)

    return activities





# SepidarApp/activity_helper.py
def get_accounting_vouchers(date_from=None, date_to=None, creator=None):
    """
    دریافت اسناد حسابداری از سپیدار
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()

        conditions = ["1=1"]
        params = []

        if date_from:
            conditions.append("CAST(v.Date AS DATE) >= ?")
            params.append(date_from)
        if date_to:
            conditions.append("CAST(v.Date AS DATE) <= ?")
            params.append(date_to)
        if creator:
            conditions.append("v.Creator = ?")
            params.append(creator)

        where = " AND ".join(conditions)

        query = f"""
            SELECT 
                v.VoucherId,
                v.Number,
                v.Date,
                v.Creator,
                v.Description,
                v.CreationDate,
                v.FiscalYearRef,
                (SELECT COUNT(*) FROM [Sepidar01].[ACC].[VoucherItem] WHERE VoucherRef = v.VoucherId) AS ItemsCount
            FROM [Sepidar01].[ACC].[Voucher] v
            WHERE {where}
            ORDER BY v.Date DESC, v.VoucherId DESC
        """

        cursor.execute(query, params)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                'id': int(row[0]),
                'number': int(row[1]) if row[1] else None,
                'date': row[2],
                'creator': int(row[3]) if row[3] else None,
                'description': row[4] or '',
                'creation_date': row[5],
                'fiscal_year_ref': int(row[6]) if row[6] else None,
                'items_count': int(row[7]) if row[7] else 0,
                'activity_type': 'accounting_voucher',
            })
        return result

    except Exception as e:
        logger.error(f"Error in get_accounting_vouchers: {e}", exc_info=True)
        return []


    