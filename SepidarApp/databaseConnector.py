import pyodbc
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """
    Singleton class for SQL Server database connection using pyodbc
    """
    _instance = None
    _connection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # جلوگیری از بازنویسی تنظیمات در بارگذاری مجدد
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._connection_string = None
            self._load_settings()
    
    def _load_settings(self):
        """بارگذاری تنظیمات از settings.py"""
        # مقادیر پیش‌فرض (مطابق با کد شما)
        self._connection_string = getattr(
            settings, 
            'SQL_SERVER_CONNECTION_STRING',
            (
                "DRIVER={ODBC Driver 17 for SQL Server};"
                "SERVER=WIN-1SSE4CQ9LKP\\AMINDB;"
                "DATABASE=AminDB1404_606876541;"
                "Trusted_Connection=yes;"
            )
        )
        
        # یا می‌توانید از تنظیمات جداگانه استفاده کنید
        self._server = getattr(settings, 'SQL_SERVER', 'WIN-1SSE4CQ9LKP\\AMINDB')
        self._database = getattr(settings, 'SQL_DATABASE', 'AminDB1404_606876541')
        self._driver = getattr(settings, 'SQL_DRIVER', '{ODBC Driver 17 for SQL Server}')
        self._trusted_connection = getattr(settings, 'SQL_TRUSTED_CONNECTION', 'yes')
        
        # ساختن connection string از تنظیمات جداگانه
        if not getattr(settings, 'SQL_USE_CONNECTION_STRING', False):
            self._connection_string = (
                f"DRIVER={self._driver};"
                f"SERVER={self._server};"
                f"DATABASE={self._database};"
                f"Trusted_Connection={self._trusted_connection};"
            )
    
    def connect(self, connection_string=None):
        """
        برقراری اتصال به پایگاه داده
        اگر connection_string داده نشود، از تنظیمات استفاده می‌کند
        """
        if self._connection is None:
            try:
                cs = connection_string or self._connection_string
                logger.info(f"🔄 Connecting to SQL Server: {self._server}")
                print(f"🔄 Connecting to SQL Server: {self._server}")
                
                self._connection = pyodbc.connect(cs)
                
                # تنظیمات اضافی برای کار با فارسی و تاریخ
                cursor = self._connection.cursor()
                cursor.execute("SET DATEFORMAT YMD")  # تنظیم فرمت تاریخ
                cursor.close()
                
                logger.info("✅ SQL Server connection established successfully")
                print("✅ SQL Server connection successful")
                return self._connection
                
            except pyodbc.Error as e:
                error_msg = f"❌ SQL Server connection failed: {e}"
                logger.error(error_msg)
                print(error_msg)
                raise
            except Exception as e:
                error_msg = f"❌ Unexpected error: {e}"
                logger.error(error_msg)
                print(error_msg)
                raise
        
        return self._connection
    
    def get_connection(self):
        """دریافت اتصال فعلی"""
        if self._connection is None:
            raise Exception("Database connection not established. Call connect() first.")
        return self._connection
    
    def get_cursor(self):
        """دریافت cursor برای اجرای کوئری"""
        conn = self.get_connection()
        return conn.cursor()
    
    def execute_query(self, query, params=None, fetch_all=True):
        """
        اجرای کوئری و برگرداندن نتایج
        - fetch_all: اگر True باشد همه نتایج را برمی‌گرداند، در غیر این صورت یک ردیف
        """
        cursor = self.get_cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # اگر کوئری SELECT باشد، نتایج را برمی‌گرداند
            if query.strip().upper().startswith('SELECT'):
                if fetch_all:
                    return cursor.fetchall()
                else:
                    return cursor.fetchone()
            else:
                # برای INSERT, UPDATE, DELETE
                cursor.commit()
                return cursor.rowcount  # تعداد ردیف‌های تحت تأثیر
                
        except pyodbc.Error as e:
            logger.error(f"Query execution error: {e}")
            cursor.rollback()
            raise
        finally:
            cursor.close()
    
    def call_procedure(self, procedure_name, params=None):
        """فراخوانی یک stored procedure"""
        cursor = self.get_cursor()
        try:
            if params:
                cursor.execute(f"{{CALL {procedure_name} ({','.join(['?' for _ in params])})}}", params)
            else:
                cursor.execute(f"{{CALL {procedure_name}}}")
            
            # اگر procedure نتایجی برگرداند
            results = []
            while True:
                if cursor.description:  # اگر نتیجه دارد
                    results.append(cursor.fetchall())
                if not cursor.nextset():  # اگر نتیجه دیگری نباشد
                    break
            
            cursor.commit()
            return results
            
        except pyodbc.Error as e:
            logger.error(f"Stored procedure error: {e}")
            cursor.rollback()
            raise
        finally:
            cursor.close()
    
    def close(self):
        """بستن اتصال"""
        if self._connection:
            try:
                self._connection.close()
                logger.info("🔒 Database connection closed")
                print("🔒 Database connection closed")
            except Exception as e:
                logger.warning(f"Error while closing connection: {e}")
            finally:
                self._connection = None
    
    def __enter__(self):
        """پشتیبانی از Context Manager (with)"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """بستن خودکار اتصال در خروج از Context Manager"""
        self.close()
    
    def is_connected(self):
        """بررسی وضعیت اتصال"""
        if self._connection:
            try:
                cursor = self._connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return True
            except:
                return False
        return False
    
    def reconnect(self):
        """بازنشانی اتصال در صورت قطع شدن"""
        self.close()
        return self.connect()

# ایجاد یک نمونه سراسری از اتصال
db = DatabaseConnection()