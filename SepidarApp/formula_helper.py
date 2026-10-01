# SepidarApp/formula_helper.py
"""
توابع کمکی برای خواندن فرمول‌ها از سپیدار
"""
import logging
from SepidarApp.databaseConnector import db

logger = logging.getLogger(__name__)


def get_all_formulas_from_sepidar() -> list:
    """
    دریافت همه فرمول‌ها از [Sepidar01].[WKO].[ProductFormula]

    Returns:
        list of dict
    """
    try:
        conn = db.get_connection()
        if conn is None:
            db.connect()
            conn = db.get_connection()

        cursor = conn.cursor()

        query = """
            SELECT 
                pf.ProductFormulaID,
                pf.Code,
                pf.Title,
                pf.ItemRef,
                pf.IsActive,
                itm.Title AS ProductName,
                itm.Code AS ProductCode
            FROM [Sepidar01].[WKO].[ProductFormula] pf
            LEFT JOIN [Sepidar01].[INV].[Item] itm 
                ON pf.ItemRef = itm.ItemID
            ORDER BY pf.Code
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        formulas = []
        for row in rows:
            formulas.append({
                'id': int(row[0]),
                'code': row[1] or '',
                'title': row[2] or '',
                'item_ref': int(row[3]) if row[3] else None,
                'is_active': bool(row[4]),
                'product_name': row[5] or '',
                'product_code': row[6] or '',
            })

        logger.info(f"✅ دریافت {len(formulas)} فرمول از سپیدار")
        return formulas

    except Exception as e:
        logger.error(f"❌ خطا در دریافت فرمول‌ها: {e}", exc_info=True)
        return []


def get_formula_ids_from_sepidar() -> set:
    """دریافت فقط ID همه فرمول‌های سپیدار (برای بررسی حذف)"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ProductFormulaID FROM [Sepidar01].[WKO].[ProductFormula]"
        )
        return {int(row[0]) for row in cursor.fetchall()}
    except Exception as e:
        logger.error(f"Error fetching formula IDs: {e}")
        return set()