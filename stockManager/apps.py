from django.apps import AppConfig


class StockmanagerConfig(AppConfig):
    name = 'stockManager'

    def ready(self):
        """
        راه‌اندازی زمان‌بند هنگام استارت اپلیکیشن
        """
        import os
        from django.conf import settings
        
        # فقط در محیط production اجرا شود

        from .scheduler import start_scheduler
        start_scheduler()