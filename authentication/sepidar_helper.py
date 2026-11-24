# authentication/sepidar_helper.py
"""
توابع کمکی برای اتصال به دیتابیس سپیدار و دریافت کد کاربر
"""
import logging
from django.conf import settings
import pyodbc
from  SepidarApp.databaseConnector import DatabaseConnection, db

logger = logging.getLogger(__name__)


def get_sepidar_code_from_db(sepidar_username:str) -> dict:
    """
    با استفاده از نام کاربری و رمز عبور، کد کاربر رو از سپیدار می‌گیره.

    Args:
        username: نام کاربری سپیدار
        password: رمز عبور سپیدار (معمولاً هش شده)

    Returns:
        dict:
          {
            'success': bool,
            'user_id': int | None,
            'message': str
          }
    """
    try:

        conn = db.get_connection()
        cursor = conn.cursor()

        # ⚠️ این کوئری رو بعد از دیدن ساختار جدول اصلاح می‌کنیم
        query = """
            SELECT TOP 1 UserID
            FROM [Sepidar01].[FMK].[User]
            WHERE UserName = ?
        """
        cursor.execute(query, (sepidar_username))
        row = cursor.fetchone()

        # cursor.close()
        # conn.close()

        if row:
            return {
                'success': True,
                'user_id': int(row[0]),
                'message': f'کد سپیدار یافت شد: {row[0]}'
            }
        else:
            return {
                'success': False,
                'user_id': None,
                'message': 'کاربری با این نام کاربری و رمز در سپیدار یافت نشد'
            }

    except pyodbc.Error as e:
        logger.error(f"Sepidar DB error: {e}")
        return {
            'success': False,
            'user_id': None,
            'message': f'خطای دیتابیس: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            'success': False,
            'user_id': None,
            'message': f'خطای غیرمنتظره: {str(e)}'
        }