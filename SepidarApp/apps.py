from django.apps import AppConfig
from .databaseConnector import db

class SepidarappConfig(AppConfig):
    name = 'SepidarApp'
    default_auto_field = 'django.db.models.BigAutoField'
    
    def ready(self):
        """اتصال به SQL Server هنگام راه‌اندازی"""
        try:
            db.connect()
            print("✅ Database connection initialized on startup")
        except Exception as e:
            print(f"⚠️ Could not connect to database on startup: {e}")