import pyodbc
import sqlite3
import logging
from datetime import datetime
import os
from decimal import Decimal
import json

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseCopier:
    """
    کلاس برای کپی دیتابیس از SQL Server به SQLite با پشتیبانی از Decimal
    """
    
    def __init__(self, sqlite_db_path='database_copy.db'):
        """
        مقداردهی اولیه
        """
        self.sqlite_path = sqlite_db_path
        self.sqlite_conn = None
        self.sqlserver_conn = None
        
    def connect_sqlserver(self):
        """
        اتصال به SQL Server
        """
        try:
            connection_string = (
                "DRIVER={ODBC Driver 17 for SQL Server};"
                "SERVER=DESKTOP-JKDSDCN\SEPIDAR;"
                "DATABASE=Sepidar01;"
                "Trusted_Connection=yes;"
            )
            self.sqlserver_conn = pyodbc.connect(connection_string)
            logger.info("✅ Connected to SQL Server successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to SQL Server: {e}")
            return False
    
    def connect_sqlite(self):
        """
        اتصال به SQLite
        """
        try:
            # حذف فایل قبلی اگر وجود دارد
            if os.path.exists(self.sqlite_path):
                os.remove(self.sqlite_path)
                logger.info(f"🗑️ Existing SQLite file removed: {self.sqlite_path}")
            
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            
            # تنظیم برای پشتیبانی از نوع‌های داده مختلف
            self.sqlite_conn.execute("PRAGMA foreign_keys = ON;")
            
            logger.info(f"✅ SQLite database created: {self.sqlite_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create SQLite database: {e}")
            return False
    
    def get_table_names(self):
        """
        دریافت لیست تمام جداول از SQL Server
        """
        try:
            cursor = self.sqlserver_conn.cursor()
            
            # دریافت جداول از دیتابیس
            query = """
                SELECT 
                    TABLE_SCHEMA,
                    TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_TYPE = 'BASE TABLE'
                AND TABLE_SCHEMA NOT IN ('sys', 'INFORMATION_SCHEMA')
                ORDER BY TABLE_NAME
            """
            
            cursor.execute(query)
            tables = cursor.fetchall()
            
            table_list = [f"{row.TABLE_SCHEMA}.{row.TABLE_NAME}" for row in tables]
            logger.info(f"📋 Found {len(table_list)} tables")
            
            return table_list
        except Exception as e:
            logger.error(f"❌ Failed to get table names: {e}")
            return []
    
    def get_table_schema(self, full_table_name):
        """
        دریافت ساختار جدول از SQL Server
        """
        try:
            parts = full_table_name.split('.')
            if len(parts) == 2:
                schema, table = parts
            else:
                schema = 'dbo'
                table = full_table_name
            
            cursor = self.sqlserver_conn.cursor()
            
            query = """
                SELECT 
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    NUMERIC_PRECISION,
                    NUMERIC_SCALE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
            """
            
            cursor.execute(query, [schema, table])
            columns = cursor.fetchall()
            
            return columns
        except Exception as e:
            logger.error(f"❌ Failed to get schema for {full_table_name}: {e}")
            return []
    
    def map_sqlserver_to_sqlite_type(self, sqlserver_type, max_length=None, precision=None, scale=None):
        """
        تبدیل نوع داده SQL Server به SQLite
        """
        sqlserver_type = sqlserver_type.lower()
        
        # انواع داده‌های عددی
        if sqlserver_type in ('int', 'bigint', 'smallint', 'tinyint'):
            return 'INTEGER'
        elif sqlserver_type in ('decimal', 'numeric', 'money', 'smallmoney'):
            return 'REAL'  # استفاده از REAL برای اعداد اعشاری
        elif sqlserver_type in ('float', 'real'):
            return 'REAL'
        
        # انواع داده‌های متنی
        elif sqlserver_type in ('varchar', 'nvarchar', 'char', 'nchar'):
            return 'TEXT'
        elif sqlserver_type in ('text', 'ntext'):
            return 'TEXT'
        
        # انواع داده‌های تاریخ و زمان
        elif sqlserver_type in ('datetime', 'datetime2', 'smalldatetime', 'date', 'time'):
            return 'TEXT'
        
        # انواع داده‌های باینری
        elif sqlserver_type in ('binary', 'varbinary', 'image'):
            return 'BLOB'
        
        # سایر انواع
        elif sqlserver_type == 'bit':
            return 'INTEGER'
        elif sqlserver_type == 'uniqueidentifier':
            return 'TEXT'
        else:
            return 'TEXT'
    
    def convert_value_for_sqlite(self, value):
        """
        تبدیل مقادیر به نوع مناسب برای SQLite
        """
        if value is None:
            return None
        
        # تبدیل Decimal به float
        if isinstance(value, Decimal):
            return float(value)
        
        # تبدیل datetime به string
        if isinstance(value, datetime):
            return value.isoformat()
        
        # تبدیل bytes به blob (داده باینری)
        if isinstance(value, bytes):
            return value
        
        # تبدیل bool به int
        if isinstance(value, bool):
            return 1 if value else 0
        
        # سایر موارد
        return value
    
    def create_table_in_sqlite(self, table_name, columns):
        """
        ایجاد جدول در SQLite با ساختار متناسب
        """
        try:
            cursor = self.sqlite_conn.cursor()
            
            # ساخت نام جدول بدون Schema
            simple_name = table_name.split('.')[-1]
            
            # ساخت کوئری CREATE TABLE
            create_query = f"CREATE TABLE IF NOT EXISTS [{simple_name}] (\n"
            
            column_definitions = []
            
            for col in columns:
                col_name = col.COLUMN_NAME
                col_type = self.map_sqlserver_to_sqlite_type(
                    col.DATA_TYPE,
                    col.CHARACTER_MAXIMUM_LENGTH,
                    col.NUMERIC_PRECISION,
                    col.NUMERIC_SCALE
                )
                
                # مدیریت NOT NULL
                nullable = "NOT NULL" if col.IS_NULLABLE == 'NO' else ""
                
                column_def = f"    [{col_name}] {col_type} {nullable}"
                column_definitions.append(column_def)
            
            create_query += ",\n".join(column_definitions)
            create_query += "\n)"
            
            # اجرای کوئری
            cursor.execute(create_query)
            self.sqlite_conn.commit()
            
            logger.info(f"✅ Table '{simple_name}' created in SQLite")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create table '{table_name}' in SQLite: {e}")
            return False
    
    def copy_data(self, table_name):
        """
        کپی داده‌ها از SQL Server به SQLite با پشتیبانی از Decimal
        """
        try:
            simple_name = table_name.split('.')[-1]
            
            # خواندن داده‌ها از SQL Server
            sqlserver_cursor = self.sqlserver_conn.cursor()
            sqlserver_cursor.execute(f"SELECT * FROM {table_name}")
            
            # دریافت ستون‌ها
            columns = [column[0] for column in sqlserver_cursor.description]
            
            # ساخت کوئری INSERT برای SQLite
            placeholders = ','.join(['?' for _ in columns])
            insert_query = f"INSERT OR REPLACE INTO [{simple_name}] ({','.join([f'[{col}]' for col in columns])}) VALUES ({placeholders})"
            
            # خواندن تمام داده‌ها
            rows = sqlserver_cursor.fetchall()
            
            if not rows:
                logger.info(f"ℹ️ No data to copy for table '{simple_name}'")
                return 0
            
            # درج داده‌ها در SQLite
            sqlite_cursor = self.sqlite_conn.cursor()
            
            # تبدیل داده‌ها به فرمت مناسب برای SQLite
            converted_rows = []
            error_count = 0
            
            for row_index, row in enumerate(rows):
                try:
                    converted_row = []
                    for i, value in enumerate(row):
                        converted_value = self.convert_value_for_sqlite(value)
                        converted_row.append(converted_value)
                    converted_rows.append(tuple(converted_row))
                except Exception as e:
                    error_count += 1
                    logger.warning(f"⚠️ Error converting row {row_index + 1} in table '{simple_name}': {e}")
                    continue
            
            if converted_rows:
                # درج داده‌ها به صورت گروهی
                sqlite_cursor.executemany(insert_query, converted_rows)
                self.sqlite_conn.commit()
                
                row_count = len(converted_rows)
                logger.info(f"✅ Copied {row_count} rows to table '{simple_name}'")
                if error_count > 0:
                    logger.warning(f"⚠️ {error_count} rows had conversion errors and were skipped")
                return row_count
            else:
                logger.warning(f"⚠️ No valid rows to copy for table '{simple_name}'")
                return 0
            
        except Exception as e:
            logger.error(f"❌ Failed to copy data for table '{table_name}': {e}")
            return 0
    
    def copy_database(self, tables_to_skip=None):
        """
        کپی کامل دیتابیس
        """
        if tables_to_skip is None:
            tables_to_skip = [
                'sysdiagrams', 
                '__EFMigrationsHistory', 
                'MigrationHistory',
                'AspNetUsers',
                'AspNetRoles'
            ]
        
        logger.info("🚀 Starting database copy process...")
        
        # اتصال به دیتابیس‌ها
        if not self.connect_sqlserver():
            return False
        
        if not self.connect_sqlite():
            self.sqlserver_conn.close()
            return False
        
        try:
            # دریافت لیست جداول
            tables = self.get_table_names()
            
            if not tables:
                logger.error("❌ No tables found in SQL Server")
                return False
            
            # فیلتر کردن جداول
            tables_to_copy = []
            for table in tables:
                simple_name = table.split('.')[-1]
                if simple_name not in tables_to_skip:
                    tables_to_copy.append(table)
            
            logger.info(f"📋 Copying {len(tables_to_copy)} tables...")
            
            # ایجاد جداول در SQLite
            for table in tables_to_copy:
                columns = self.get_table_schema(table)
                if columns:
                    self.create_table_in_sqlite(table, columns)
            
            # کپی داده‌ها
            total_rows = 0
            successful_tables = 0
            
            for table in tables_to_copy:
                rows = self.copy_data(table)
                if rows > 0:
                    total_rows += rows
                    successful_tables += 1
            
            logger.info(f"✅ Database copy completed successfully!")
            logger.info(f"📊 Copied {successful_tables}/{len(tables_to_copy)} tables with {total_rows} total rows")
            logger.info(f"💾 SQLite database saved at: {self.sqlite_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during database copy: {e}")
            return False
        finally:
            # بستن اتصالات
            if self.sqlserver_conn:
                self.sqlserver_conn.close()
            if self.sqlite_conn:
                self.sqlite_conn.close()

    def copy_specific_tables(self, tables_to_copy):
        """
        کپی فقط جداول مشخص شده
        """
        logger.info(f"🚀 Starting copy for {len(tables_to_copy)} specific tables...")
        
        if not self.connect_sqlserver():
            return False
        
        if not self.connect_sqlite():
            self.sqlserver_conn.close()
            return False
        
        try:
            successful_tables = 0
            total_rows = 0
            
            for table in tables_to_copy:
                logger.info(f"📋 Copying table: {table}")
                
                # دریافت ساختار
                columns = self.get_table_schema(table)
                if columns:
                    self.create_table_in_sqlite(table, columns)
                
                # کپی داده‌ها
                rows = self.copy_data(table)
                if rows > 0:
                    total_rows += rows
                    successful_tables += 1
            
            logger.info(f"✅ Copy completed! {successful_tables}/{len(tables_to_copy)} tables copied with {total_rows} rows")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return False
        finally:
            if self.sqlserver_conn:
                self.sqlserver_conn.close()
            if self.sqlite_conn:
                self.sqlite_conn.close()

    def create_backup(self):
        """
        ایجاد بکاپ با تاریخ در نام فایل
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'database_backup_{timestamp}.db'
        
        copier = DatabaseCopier(backup_path)
        success = copier.copy_database()
        
        if success:
            logger.info(f"✅ Backup created: {backup_path}")
            return backup_path
        else:
            logger.error("❌ Backup creation failed")
            return None

# اجرای اصلی
if __name__ == "__main__":
    import sys
    
    # کپی کامل دیتابیس
    copier = DatabaseCopier('my_database_copy.db')
    copier.copy_database()
    
    # یا کپی فقط جداول خاص
    # tables = ['WKO.ProductFormula', 'WKO.FormulaBomItem', 'INV.Item']
    # copier.copy_specific_tables(tables)