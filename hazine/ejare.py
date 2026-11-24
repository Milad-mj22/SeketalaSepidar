# -*- coding: utf-8 -*-
"""
استخراج هزینه‌های غیرمستقیم (سربار) از سپیدار
- منبع: ACC.VoucherItem (اسناد حسابداری واقعی)
- به تفکیک: حساب + مرکز هزینه
"""

import pyodbc
import socket

import arabic_reshaper
from bidi.algorithm import get_display


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


def separator(char="=", n=95):
    print(char * n)


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
# 📋 حساب‌های هزینه‌ای / سربار
# ============================================================
def find_overhead_accounts(conn):
    query = """
    SELECT 
        a.AccountId,
        a.Code,
        a.Title,
        a.Title_En,
        a.Type,
        a.IsActive
    FROM [Sepidar01].[ACC].[Account] a
    WHERE (
        a.Title LIKE N'%سربار%'
        OR a.Title LIKE N'%غیرمستقیم%'
        OR a.Title LIKE N'%هزینه%'
        OR a.Title LIKE N'%اجاره%'
        OR a.Title LIKE N'%حقوق%'
        OR a.Title LIKE N'%دستمزد%'
        OR a.Title LIKE N'%آب%'
        OR a.Title LIKE N'%برق%'
        OR a.Title LIKE N'%گاز%'
        OR a.Title LIKE N'%تلفن%'
        OR a.Title LIKE N'%حمل%'
        OR a.Title LIKE N'%نگهداری%'
        OR a.Title LIKE N'%تعمیر%'
        OR a.Title LIKE N'%استهلاک%'
        OR a.Title LIKE N'%عوارض%'
    )
    AND a.IsActive = 1
    ORDER BY a.Code
    """
    cursor = conn.cursor()
    cursor.execute(query)
    cols = [c[0] for c in cursor.description]
    rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    cursor.close()
    return rows


# ============================================================
# 📋 مراکز هزینه
# ============================================================
def get_cost_centers(conn):
    query = """
    SELECT 
        CostCenterId, DLCode, DLTitle, DLTitle_En,
        DLRef, DLType, Type, IsActive
    FROM [Sepidar01].[GNR].[vwCostCenter]
    WHERE IsActive = 1
    ORDER BY Type, DLCode
    """
    cursor = conn.cursor()
    cursor.execute(query)
    cols = [c[0] for c in cursor.description]
    rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    cursor.close()
    return rows


# ============================================================
# 📋 ریز تراکنش‌ها  ← اصلاح‌شده با AccountSLRef
# ============================================================
def get_overhead_transactions(conn, account_ids=None,
                               date_from=None, date_to=None,
                               cost_center_ids=None):
    conditions = ["vi.Debit > 0"]
    params = []

    if account_ids:
        ph = ",".join("?" * len(account_ids))
        conditions.append(f"vi.AccountSLRef IN ({ph})")
        params.extend(account_ids)

    if date_from:
        conditions.append("v.Date >= ?")
        params.append(date_from)

    if date_to:
        conditions.append("v.Date <= ?")
        params.append(date_to)

    if cost_center_ids:
        ph = ",".join("?" * len(cost_center_ids))
        conditions.append(f"vi.DLRef IN ({ph})")
        params.extend(cost_center_ids)

    where = " AND ".join(conditions)

    query = f"""
    SELECT 
        v.VoucherId,
        v.Number AS VoucherNumber,
        v.Date AS VoucherDate,
        v.Description AS VoucherDescription,
        vi.VoucherItemId,
        vi.AccountSLRef,
        a.Code AS AccountCode,
        a.Title AS AccountTitle,
        vi.DLRef AS CostCenterRef,
        cc.DLCode AS CostCenterCode,
        cc.DLTitle AS CostCenterTitle,
        cc.Type AS CostCenterType,
        vi.Debit,
        vi.Credit,
        vi.Description AS ItemDescription
    FROM [Sepidar01].[ACC].[VoucherItem] vi
    INNER JOIN [Sepidar01].[ACC].[Voucher] v 
        ON vi.VoucherRef = v.VoucherId
    LEFT JOIN [Sepidar01].[ACC].[Account] a 
        ON vi.AccountSLRef = a.AccountId
    LEFT JOIN [Sepidar01].[GNR].[vwCostCenter] cc 
        ON vi.DLRef = cc.CostCenterId
    WHERE {where}
    ORDER BY v.Date DESC, v.Number DESC
    """
    cursor = conn.cursor()
    cursor.execute(query, params)
    cols = [c[0] for c in cursor.description]
    rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    cursor.close()
    return rows


# ============================================================
# 📊 جمع سربار به تفکیک مرکز هزینه  ← اصلاح‌شده
# ============================================================
def summarize_overhead_by_cc(conn, account_ids=None,
                              date_from=None, date_to=None):
    conditions = ["vi.Debit > 0"]
    params = []

    if account_ids:
        ph = ",".join("?" * len(account_ids))
        conditions.append(f"vi.AccountSLRef IN ({ph})")
        params.extend(account_ids)

    if date_from:
        conditions.append("v.Date >= ?")
        params.append(date_from)

    if date_to:
        conditions.append("v.Date <= ?")
        params.append(date_to)

    where = " AND ".join(conditions)

    query = f"""
    SELECT 
        cc.CostCenterId,
        cc.DLCode AS CostCenterCode,
        cc.DLTitle AS CostCenterTitle,
        cc.Type AS CostCenterType,
        COUNT(DISTINCT v.VoucherId) AS VoucherCount,
        SUM(vi.Debit) AS TotalDebit,
        SUM(vi.Credit) AS TotalCredit,
        SUM(vi.Debit - vi.Credit) AS NetAmount
    FROM [Sepidar01].[ACC].[VoucherItem] vi
    INNER JOIN [Sepidar01].[ACC].[Voucher] v 
        ON vi.VoucherRef = v.VoucherId
    LEFT JOIN [Sepidar01].[GNR].[vwCostCenter] cc 
        ON vi.DLRef = cc.CostCenterId
    WHERE {where}
    GROUP BY cc.CostCenterId, cc.DLCode, cc.DLTitle, cc.Type
    ORDER BY cc.Type, cc.DLCode
    """
    cursor = conn.cursor()
    cursor.execute(query, params)
    cols = [c[0] for c in cursor.description]
    rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    cursor.close()
    return rows


# ============================================================
# 📊 جمع سربار به تفکیک حساب  ← اصلاح‌شده
# ============================================================
def summarize_overhead_by_account(conn, account_ids=None,
                                   date_from=None, date_to=None):
    conditions = ["vi.Debit > 0"]
    params = []

    if account_ids:
        ph = ",".join("?" * len(account_ids))
        conditions.append(f"vi.AccountSLRef IN ({ph})")
        params.extend(account_ids)

    if date_from:
        conditions.append("v.Date >= ?")
        params.append(date_from)

    if date_to:
        conditions.append("v.Date <= ?")
        params.append(date_to)

    where = " AND ".join(conditions)

    query = f"""
    SELECT 
        a.AccountId,
        a.Code AS AccountCode,
        a.Title AS AccountTitle,
        COUNT(DISTINCT v.VoucherId) AS VoucherCount,
        SUM(vi.Debit) AS TotalDebit
    FROM [Sepidar01].[ACC].[VoucherItem] vi
    INNER JOIN [Sepidar01].[ACC].[Voucher] v 
        ON vi.VoucherRef = v.VoucherId
    LEFT JOIN [Sepidar01].[ACC].[Account] a 
        ON vi.AccountSLRef = a.AccountId
    WHERE {where}
    GROUP BY a.AccountId, a.Code, a.Title
    HAVING SUM(vi.Debit) > 0
    ORDER BY SUM(vi.Debit) DESC
    """
    cursor = conn.cursor()
    cursor.execute(query, params)
    cols = [c[0] for c in cursor.description]
    rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
    cursor.close()
    return rows


# ============================================================
# 🚀 Main
# ============================================================
def main():
    db = DatabaseConnection()
    db.connect()
    conn = db.get_connection()

    try:
        # ---- 1) حساب‌های هزینه‌ای ----
        separator("=")
        fp("📋 1) حساب‌های هزینه‌ای / سربار")
        separator("=")

        overhead_accounts = find_overhead_accounts(conn)
        fp(f"  {len(overhead_accounts)} حساب پیدا شد:\n")
        fp(f"{'#':<4} {'ID':<6} {'کد':<12} {'نام':<55}")
        separator("-", 95)
        for idx, acc in enumerate(overhead_accounts, 1):
            fp(f"  {idx:<4} {acc['AccountId']:<6} "
               f"{acc['Code'] or '-':<12} {(acc['Title'] or '-')[:53]:<55}")

        # ---- 2) مراکز هزینه ----
        print()
        separator("=")
        fp("📋 2) مراکز هزینه فعال")
        separator("=")

        cost_centers = get_cost_centers(conn)
        type_map = {1: 'تولیدی', 2: 'اداری/تشکیلاتی',
                    3: 'خدماتی', 4: 'عمومی'}

        fp(f"{'ID':<5} {'کد':<10} {'نام':<40} {'نوع':<15}")
        separator("-", 90)
        for cc in cost_centers:
            t = type_map.get(cc['Type'], f"نوع {cc['Type']}")
            fp(f"  {cc['CostCenterId']:<5} {cc['DLCode'] or '-':<10} "
               f"{(cc['DLTitle'] or '-')[:38]:<40} {t:<15}")

        # ---- 3) جمع سربار به تفکیک حساب ----
        print()
        separator("=")
        fp("💰 3) جمع هزینه‌ها به تفکیک حساب (از ACC.VoucherItem)")
        separator("=")

        account_ids = [a['AccountId'] for a in overhead_accounts]

        summary_acc = summarize_overhead_by_account(
            conn, account_ids=account_ids
        )

        if summary_acc:
            fp(f"{'#':<4} {'کد':<10} {'نام حساب':<45} "
               f"{'تعداد سند':>10} {'مبلغ (ریال)':>20}")
            separator("-", 95)

            total = 0
            for idx, row in enumerate(summary_acc, 1):
                amount = float(row['TotalDebit'] or 0)
                total += amount
                title = (row['AccountTitle'] or '-')[:43]
                fp(f"  {idx:<4} {row['AccountCode'] or '-':<10} "
                   f"{title:<45} {row['VoucherCount']:>10} "
                   f"{amount:>20,.0f}")

            separator("-", 95)
            fp(f"  {'':<4} {'':<10} {'جمع کل:':<45} {'':>10} "
               f"{total:>20,.0f}")
        else:
            fp("  ⚠️ هیچ تراکنش سرباری پیدا نشد.")

        # ---- 4) جمع سربار به تفکیک مرکز هزینه ----
        print()
        separator("=")
        fp("📊 4) جمع سربار به تفکیک مرکز هزینه")
        separator("=")

        summary_cc = summarize_overhead_by_cc(
            conn, account_ids=account_ids
        )

        if summary_cc:
            fp(f"{'#':<4} {'کد':<10} {'مرکز هزینه':<35} "
               f"{'نوع':<15} {'تعداد':>8} {'مبلغ':>20}")
            separator("-", 95)

            total = 0
            for idx, row in enumerate(summary_cc, 1):
                if not row['NetAmount']:
                    continue
                amount = float(row['NetAmount'])
                total += amount
                t = type_map.get(row['CostCenterType'],
                                 f"نوع {row['CostCenterType']}")
                title = (row['CostCenterTitle'] or 'بدون مرکز')[:33]
                code = row['CostCenterCode'] or '-'
                fp(f"  {idx:<4} {code:<10} {title:<35} "
                   f"{t:<15} {row['VoucherCount']:>8} "
                   f"{amount:>20,.0f}")

            separator("-", 95)
            fp(f"  {'':<4} {'':<10} {'جمع کل:':<35} {'':<15} {'':>8} "
               f"{total:>20,.0f}")
        else:
            fp("  ⚠️ داده‌ای پیدا نشد.")

        # ---- 5) نمونه ریز تراکنش‌ها ----
        print()
        separator("=")
        fp("📋 5) نمونه ریز تراکنش‌های سربار (۲۰ مورد آخر)")
        separator("=")

        details = get_overhead_transactions(
            conn, account_ids=account_ids
        )[:20]

        if details:
            fp(f"{'تاریخ':<12} {'شماره':<8} {'حساب':<30} "
               f"{'مرکز هزینه':<25} {'مبلغ':>15}")
            separator("-", 95)

            for d in details:
                date_str = (d['VoucherDate'].strftime('%Y/%m/%d')
                            if d['VoucherDate'] else '-')
                acc = (d['AccountTitle'] or '-')[:28]
                cc = (d['CostCenterTitle'] or '-')[:23]
                debit = float(d['Debit'] or 0)
                fp(f"{date_str:<12} {d['VoucherNumber']:<8} "
                   f"{acc:<30} {cc:<25} {debit:>15,.0f}")
        else:
            fp("  ⚠️ تراکنشی پیدا نشد.")

    finally:
        db.close()


if __name__ == "__main__":
    main()