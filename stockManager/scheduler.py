# your_app/scheduler.py
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django.utils import timezone
import pytz
from stockManager.utils import prepare_materials2send_sms
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
TEST = False


# ============================================
# تنظیم منطقه زمانی ایران
# ============================================
IRAN_TIMEZONE = pytz.timezone('Asia/Tehran')

# حالت تست
TEST = False  # برای تست True کنید

def start_scheduler():
    """
    راه‌اندازی زمان‌بند برای اجرای روزانه با ساعت ایران
    """
    print("=" * 60)
    print("🔄 Starting scheduler...")
    
    # نمایش زمان فعلی به وقت ایران
    current_time = datetime.now(IRAN_TIMEZONE)
    print(f"📅 Current time (Iran): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌍 Timezone: {IRAN_TIMEZONE}")
    print("=" * 60)
    
    logger.info("🔄 Starting scheduler...")
    logger.info(f"📅 Current time (Iran): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # ایجاد زمان‌بند با Timezone ایران
        scheduler = BackgroundScheduler(timezone=IRAN_TIMEZONE)
        scheduler.add_jobstore(DjangoJobStore(), 'default')
        
        # ============================================
        # حالت تست: اجرا در ۱۰ ثانیه دیگر
        # ============================================
        if TEST:
            run_time = datetime.now(IRAN_TIMEZONE) + timedelta(seconds=10)
            
            scheduler.add_job(
                process_daily_material_adjustment_job,
                trigger='date',
                run_date=run_time,
                id='daily_material_adjustment_test',
                max_instances=1,
                replace_existing=True,
            )
            
            print(f" TEST MODE: Job will run at {run_time.strftime('%Y-%m-%d %H:%M:%S')} (Iran time)")
            logger.info(f" TEST MODE: Job will run at {run_time.strftime('%Y-%m-%d %H:%M:%S')} (Iran time)")
        
        # ============================================
        # حالت عادی: اجرا هر روز ساعت ۱۸:۰۰ به وقت ایران
        # ============================================
        else:
            # تنظیم زمان به وقت ایران
            HOUR = 19   # ساعت ۱۸
            MINUTE = 5  # دقیقه ۰
            
            print(f" Setting daily job at {HOUR:02d}:{MINUTE:02d} (Iran time)")
            logger.info(f" Setting daily job at {HOUR:02d}:{MINUTE:02d} (Iran time)")
            
            # محاسبه زمان بعدی اجرا برای نمایش
            next_run = get_next_run_time(HOUR, MINUTE)
            if next_run:
                print(f"📅 Next execution: {next_run.strftime('%Y-%m-%d %H:%M:%S')} (Iran time)")
                logger.info(f" Next execution: {next_run.strftime('%Y-%m-%d %H:%M:%S')} (Iran time)")
            
            scheduler.add_job(
                process_daily_material_adjustment_job,
                trigger=CronTrigger(
                    hour=HOUR,
                    minute=MINUTE,
                    timezone=IRAN_TIMEZONE
                ),
                id='daily_material_adjustment',
                max_instances=1,
                replace_existing=True,
            )
            
            print(f"⏰ Scheduler started - Daily job at {HOUR:02d}:{MINUTE:02d} (Iran time)")
            logger.info(f" Scheduler started - Daily job at {HOUR:02d}:{MINUTE:02d} (Iran time)")
        
        # ============================================
        # شروع زمان‌بند
        # ============================================
        scheduler.start()
        
        # ============================================
        # نمایش وضعیت jobها
        # ============================================
        jobs = scheduler.get_jobs()
        print(f"\n📋 Jobs in scheduler: {len(jobs)}")
        for job in jobs:
            print(f"   - ID: {job.id}")
            if job.next_run_time:
                # تبدیل به وقت ایران
                iran_time = job.next_run_time.astimezone(IRAN_TIMEZONE)
                print(f"     Next run: {iran_time.strftime('%Y-%m-%d %H:%M:%S')} (Iran time)")
            print(f"     Trigger: {job.trigger}")
            logger.info(f"   - {job.id}: next run at {job.next_run_time}")
        
        print("\n" + "=" * 60)
        print("✅ Scheduler started successfully!")
        print("=" * 60)
        
        return scheduler
        
    except Exception as e:
        print(f"❌ Failed to start scheduler: {e}")
        logger.error(f"[Error] Failed to start scheduler: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_next_run_time(hour, minute):
    """
    محاسبه زمان بعدی اجرا بر اساس ساعت و دقیقه
    """
    from datetime import datetime, timedelta
    
    now = datetime.now(IRAN_TIMEZONE)
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    if next_run <= now:
        next_run += timedelta(days=1)
    
    return next_run

def process_daily_material_adjustment_job():
    """
    تابعی که هر روز ساعت ۱۸ اجرا می‌شود
    """
    # from .tasks import process_daily_material_adjustment
    
    logger.info(f"⏰ Running daily job at {timezone.now()}")
    
    try:
        result = prepare_materials2send_sms()# process_daily_material_adjustment()
        logger.info(f"[OK] Daily job completed: {result}")
        
        # ثبت تاریخچه اجرا
        from .models import DailyJobLog
        DailyJobLog.objects.create(
            executed_at=timezone.now(),
            status='success' if result.get('success') else 'failed',
            message=result.get('message', ''),
            result=result
        )
        
    except Exception as e:
        logger.error(f"[Error] Daily job failed: {e}")
        from .models import DailyJobLog
        DailyJobLog.objects.create(
            executed_at=timezone.now(),
            status='failed',
            message=str(e)
        )