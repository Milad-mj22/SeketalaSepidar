# your_app/scheduler.py
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django.utils import timezone

from stockManager.utils import prepare_materiasl2send_sms

logger = logging.getLogger(__name__)

def start_scheduler():
    print('start_scheduler ')
    """
    راه‌اندازی زمان‌بند برای اجرای روزانه
    """
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), 'default')
    
    # ============================================
    # 🔧 برای تست: اجرا در ۱۰ ثانیه دیگر
    # ============================================
    from datetime import datetime, timedelta
    run_time = datetime.now() + timedelta(seconds=10)
    
    scheduler.add_job(
        process_daily_material_adjustment_job,
        trigger='date',  # اجرا در یک زمان مشخص
        run_date=run_time,
        id='daily_material_adjustment_test',
        max_instances=1,
        replace_existing=True,
    )
    
    scheduler.start()
    logger.info("⏰ Scheduler started - Daily job at 18:00")


def process_daily_material_adjustment_job():
    """
    تابعی که هر روز ساعت ۱۸ اجرا می‌شود
    """
    # from .tasks import process_daily_material_adjustment
    
    logger.info(f"⏰ Running daily job at {timezone.now()}")
    
    try:
        result = prepare_materiasl2send_sms()# process_daily_material_adjustment()
        logger.info(f"✅ Daily job completed: {result}")
        
        # ثبت تاریخچه اجرا
        from .models import DailyJobLog
        DailyJobLog.objects.create(
            executed_at=timezone.now(),
            status='success' if result.get('success') else 'failed',
            message=result.get('message', ''),
            result=result
        )
        
    except Exception as e:
        logger.error(f"❌ Daily job failed: {e}")
        from .models import DailyJobLog
        DailyJobLog.objects.create(
            executed_at=timezone.now(),
            status='failed',
            message=str(e)
        )