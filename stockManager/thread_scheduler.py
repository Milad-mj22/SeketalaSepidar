# stockManager/thread_scheduler.py
import threading
import time
import logging
from datetime import datetime
from django.conf import settings
import requests

logger = logging.getLogger(__name__)

# رویداد برای توقف ترد
_stop_event = threading.Event()
_scheduler_thread = None


def _scheduler_worker(interval_seconds=3600):
    """
    Worker که هر interval_seconds یکبار تابع را اجرا می‌کند
    """
    return
    from .scheduler import collect_and_send_low_stock_data
    
    logger.info(f"Scheduler thread started - interval: {interval_seconds}s")
    
    while not _stop_event.is_set():
        try:
            logger.info("Running scheduled task...")
            result = collect_and_send_low_stock_data()
            logger.info(f"Task result: {result}")
        except Exception as e:
            logger.error(f"Error in scheduler worker: {e}", exc_info=True)
        
        # انتظار برای interval بعدی (با قابلیت توقف سریع)
        _stop_event.wait(timeout=interval_seconds)
    
    logger.info("Scheduler thread stopped")


def start_thread_scheduler(interval_seconds=3600):
    """شروع ترد زمان‌بند"""
    global _scheduler_thread
    
    if _scheduler_thread and _scheduler_thread.is_alive():
        logger.warning("Scheduler thread is already running")
        return
    
    _stop_event.clear()
    _scheduler_thread = threading.Thread(
        target=_scheduler_worker,
        args=(interval_seconds,),
        daemon=True,  # daemon تا با خروج برنامه متوقف شود
        name="LowStockSchedulerThread"
    )
    _scheduler_thread.start()
    logger.info("Scheduler thread started successfully")


def stop_thread_scheduler():
    """توقف ترد زمان‌بند"""
    global _scheduler_thread
    
    if _scheduler_thread and _scheduler_thread.is_alive():
        _stop_event.set()
        _scheduler_thread.join(timeout=5)
        logger.info("Scheduler thread stopped")