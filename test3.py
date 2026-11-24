# -*- coding: utf-8 -*-
"""
کاوش دیتابیس سپیدار - نسخه مستقل (بدون نیاز به Django)
ذخیره خروجی در فایل متنی + چاپ در کنسول
"""

import socket
import io
import sys
import datetime
import pyodbc
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


# ============================================================
# 📝 کلاس Tee: همزمان در کنسول و فایل بنویس
# ============================================================
class Tee:
    """همزمان به چند stream می‌نویسد (کنسول + فایل)"""

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
# کلاس اتصال (مستقل از Django)
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
            if 'DESKTOP' in pc_name:
                SQL_SERVER = pc_name
            else:
                SQL_SERVER = 'DESKTOP-JKDSDCN\\SEPIDAR'
                SQL_SERVER = "DESKTOP-OCIN559"

            self._server = SQL_SERVER
            self._database = "Sepidar01"
            self._driver = "{ODBC Driver 17 for SQL Server}"
            self._trusted_connection = "yes"

            self._connection_string = (
                f"DRIVER={self._driver};"
                f"SERVER={self._server};"
                f"DATABASE={self._database};"
                f"Trusted_Connection={self._trusted_connection};"
            )
            # اگر با یوزر/پسورد وصل می‌شی:
            # self._connection_string = (
            #     f"DRIVER={self._driver};"
            #     f"SERVER={self._server};"
            #     f"DATABASE={self._database};"
            #     f"UID=sa;PWD=YourPassword;"
            # )

    def connect(self):
        if self._connection is None:
            try:
                print(f"🔄 Connecting to SQL Server: {self._server}")
                self._connection = pyodbc.connect(self._connection_string)
                cur = self._connection.cursor()
                cur.execute("SET DATEFORMAT YMD")
                cur.close()
                print("✅ SQL Server connection successful")
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                raise
        return self._connection

    def get_connection(self):
        if self._connection is None:
            self.connect()
        return self._connection

    def execute_query(self, query, params=None):
        cursor = self.get_connection().cursor()
        try:
            cursor.execute(query, params) if params else cursor.execute(query)
            return cursor.fetchall()
        finally:
            cursor.close()

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None
            print("🔒 Connection closed")


# ============================================================
# 🔧 توابع کمکی
# ============================================================
def section(title):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)


def safe_read_sql(conn, query, title=""):
    """اجرای کوئری با pandas و مدیریت خطا"""
    try:
        df = pd.read_sql(query, conn)
        print(df.to_string(index=False))
        return df
    except Exception as e:
        print(f"⚠️ خطا در [{title}]: {e}")
        return None


def run_exploration(conn):
    """تمام ۱۰ بخش کاوش رو اجرا می‌کنه"""

    # ---------- 1 ----------
    section("📋 1) جدول‌های مرتبط با Product / Formula / BOM / Item / Price / Cost")
    safe_read_sql(conn, """
        SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME LIKE '%Product%'
           OR TABLE_NAME LIKE '%Formula%'
           OR TABLE_NAME LIKE '%BOM%'
           OR TABLE_NAME LIKE '%Item%'
           OR TABLE_NAME LIKE '%Price%'
           OR TABLE_NAME LIKE '%Cost%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """, "بخش 1")

    # ---------- 2 ----------
    section("🏗️ 2) ساختار WKO.vwProductFormula")
    safe_read_sql(conn, """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA='WKO' AND TABLE_NAME='vwProductFormula'
        ORDER BY ORDINAL_POSITION
    """, "بخش 2")

    # ---------- 3 ----------
    section("🏗️ 3) ساختار WKO.FormulaBomItem")
    safe_read_sql(conn, """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA='WKO' AND TABLE_NAME='FormulaBomItem'
        ORDER BY ORDINAL_POSITION
    """, "بخش 3")

    # ---------- 4 ----------
    section("🏗️ 4) ساختار INV.Item")
    safe_read_sql(conn, """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA='INV' AND TABLE_NAME='Item'
        ORDER BY ORDINAL_POSITION
    """, "بخش 4")

    # ---------- 5 ----------
    section("📊 5) نمونه فرمول‌ها (vwProductFormula)")
    safe_read_sql(conn, """
        SELECT TOP 5 *
        FROM [Sepidar01].[WKO].[vwProductFormula]
        ORDER BY ProductFormulaID DESC
    """, "بخش 5")

    # ---------- 6 ----------
    section("📊 6) نمونه مواد (FormulaBomItem)")
    safe_read_sql(conn, """
        SELECT TOP 20 *
        FROM [Sepidar01].[WKO].[FormulaBomItem]
        ORDER BY ProductFormulaRef DESC
    """, "بخش 6")

    # ---------- 7 ----------
    section("💰 7) View های مرتبط با Price / Cost / BOM / Inventory / Stock")
    safe_read_sql(conn, """
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_NAME LIKE '%Price%'
           OR TABLE_NAME LIKE '%Cost%'
           OR TABLE_NAME LIKE '%BOM%'
           OR TABLE_NAME LIKE '%Inventory%'
           OR TABLE_NAME LIKE '%Stock%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """, "بخش 7")

    # ---------- 8 ----------
    section("💵 8) جدول‌های خرید/فاکتور (Invoice/Receipt/Purchase)")
    safe_read_sql(conn, """
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME LIKE '%Invoice%'
           OR TABLE_NAME LIKE '%Receipt%'
           OR TABLE_NAME LIKE '%Purchase%'
           OR TABLE_NAME LIKE '%InventoryReceipt%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """, "بخش 8")

    # ---------- 9 ----------
    section("📚 9) تمام جداول Schema های INV / WKO / GNR / ACC / FMK")
    safe_read_sql(conn, """
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA IN ('INV','WKO','GNR','ACC','FMK')
        ORDER BY TABLE_SCHEMA, TABLE_NAME
    """, "بخش 9")

    # ---------- 10 ----------
    section("🔍 10) هر ستونی که اسمش شامل Price / Cost / Fee / Rate باشه (کل DB)")
    df = safe_read_sql(conn, """
        SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE COLUMN_NAME LIKE '%Price%'
           OR COLUMN_NAME LIKE '%Cost%'
           OR COLUMN_NAME LIKE '%Fee%'
           OR COLUMN_NAME LIKE '%Rate%'
        ORDER BY TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME
    """, "بخش 10")
    if df is not None:
        print(f"\n📌 مجموع: {len(df)} ستون قیمت/هزینه پیدا شد")


# ============================================================
# 🚀 اجرا
# ============================================================
def main():
    # ---- نام فایل خروجی با تاریخ و ساعت ----
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = f"db_exploration_{ts}.txt"

    # ---- فایل با انکودینگ utf-8 ----
    f = open(out_file, "w", encoding="utf-8")

    # ---- ذخیره stream اصلی ----
    original_stdout = sys.stdout

    # ---- فعال‌سازی Tee ----
    sys.stdout = Tee(original_stdout, f)

    try:
        print("=" * 75)
        print(f"  🗄️ کاوش دیتابیس سپیدار")
        print(f"  🕐 زمان اجرا: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 75)

        db = DatabaseConnection()
        db.connect()
        conn = db.get_connection()

        run_exploration(conn)

        db.close()

        print("\n✅ تمام شد")
        print(f"📁 فایل خروجی: {out_file}")

    except Exception as e:
        print(f"\n❌ خطای کلی: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # ---- بازگرداندن stdout ----
        sys.stdout = original_stdout
        f.close()

        # ---- پیام نهایی در کنسول ----
        print(f"\n🎉 خروجی در فایل ذخیره شد: {out_file}")
        print(f"   (همین فایل رو برام بفرست)")


if __name__ == "__main__":
    main()