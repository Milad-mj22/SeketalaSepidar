from django.apps import AppConfig
import os
import logging


logger = logging.getLogger(__name__)


class StockmanagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stockManager'
    
    def ready(self):
        """
        شروع ترد زمان‌بند هنگام آماده شدن اپلیکیشن
        """
        # جلوگیری از اجرای چندباره در حالت development (runserver)
        # Django در حالت runserver دو پروسه اجرا می‌کند:
        # 1. پروسه اصلی (reloader) - RUN_MAIN ست نشده
        # 2. پروسه فرزند (actual server) - RUN_MAIN = 'true'
        # ما فقط در پروسه فرزند ترد را شروع می‌کنیم
        
        if os.environ.get('RUN_MAIN') == 'true':
            # حالت development با runserver
            self._start_scheduler()
        elif os.environ.get('RUN_MAIN') is None and not self._is_management_command():
            # حالت production (gunicorn/uwsgi) - RUN_MAIN ست نشده
            self._start_scheduler()
    
    def _is_management_command(self):
        """بررسی اینکه آیا دستور manage.py در حال اجراست"""
        import sys
        management_commands = [
            'migrate', 'makemigrations', 'collectstatic', 
            'shell', 'test', 'createsuperuser', 'loaddata',
            'dumpdata', 'flush', 'showmigrations'
        ]
        return any(cmd in sys.argv for cmd in management_commands)
    
    def _start_scheduler(self):
        """شروع امن ترد زمان‌بند"""
        try:
            from .thread_scheduler import start_thread_scheduler
            from stockManager.scheduler import start_scheduler

            start_thread_scheduler(interval_seconds=3600)  # هر 1 ساعت
            start_scheduler()
            logger.info("✓ Low stock scheduler thread started")
        except Exception as e:
            logger.error(f"✗ Failed to start scheduler thread: {e}", exc_info=True)