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








from django.conf import settings
import requests


def collect_and_send_low_stock_data():
    """
    جمع‌آوری داده‌های کمبود موجودی از دیتابیس سپیدار
    و ارسال به سایت seketalamanager.ir
    این تابع در یک ترد جداگانه اجرا می‌شود
    """
    from SepidarApp.databaseConnector import db
    
    logger.info("=" * 60)
    logger.info(f"Starting low stock data collection at {datetime.now()}")
    
    try:
        # اتصال به دیتابیس خارجی
        db.connect()
        ext_conn = db.get_connection()
        cursor = ext_conn.cursor()
        
        query = """
        SELECT 
            i.Code,
            i.Title,
            i.Title_En,
            i.MinimumAmount,
            i.DefaultStockRef,
            i.UnitRef,
            u.Title AS UnitTitle,
            
            -- موجودی در انبار پیش‌فرض (10)
            ISNULL((
                SELECT SUM(Quantity)
                FROM [Sepidar01].[INV].[ItemStockSummary] iss
                WHERE iss.ItemRef = i.ItemID
                  AND iss.StockRef = 10
                  AND iss.FiscalYearRef = (
                      SELECT MAX(FiscalYearRef) 
                      FROM [Sepidar01].[INV].[ItemStockSummary] 
                      WHERE ItemRef = i.ItemID
                  )
            ), 0) AS DefaultStockQuantity,
            
            -- موجودی در تمام انبارها (آخرین سال مالی)
            ISNULL((
                SELECT SUM(Quantity)
                FROM [Sepidar01].[INV].[ItemStockSummary] iss
                WHERE iss.ItemRef = i.ItemID
                  AND iss.FiscalYearRef = (
                      SELECT MAX(FiscalYearRef) 
                      FROM [Sepidar01].[INV].[ItemStockSummary] 
                      WHERE ItemRef = i.ItemID
                  )
            ), 0) AS TotalStockQuantity,
            
            -- لیست موجودی در همه انبارها با جزئیات
            STUFF((
                SELECT ', ' + 
                    CAST(s.Code AS VARCHAR) + ':' + 
                    CAST(ISNULL(iss.Quantity, 0) AS VARCHAR)
                FROM [Sepidar01].[INV].[Stock] s
                INNER JOIN [Sepidar01].[INV].[ItemStockSummary] iss 
                    ON iss.StockRef = s.StockID 
                    AND iss.ItemRef = i.ItemID
                    AND iss.FiscalYearRef = (
                        SELECT MAX(FiscalYearRef) 
                        FROM [Sepidar01].[INV].[ItemStockSummary] 
                        WHERE ItemRef = i.ItemID
                    )
                WHERE s.IsActive = 1
                ORDER BY s.Code
                FOR XML PATH('')
            ), 1, 2, '') AS StockDetails

        FROM [Sepidar01].[INV].[Item] i
        LEFT JOIN [Sepidar01].[INV].[Unit] u 
            ON i.UnitRef = u.UnitID

        WHERE i.DefaultStockRef = 10
          AND i.IsActive = 1

        ORDER BY i.Code;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        low_stock_items = []
        total_items = 0
        
        for row in results:
            total_stock = float(row[8]) if row[8] else 0
            default_stock = float(row[7]) if row[7] else 0
            minimum_amount = float(row[3]) if row[3] else 0
            
            # فقط مواردی که موجودی کمتر از حداقل است
            if default_stock < minimum_amount:
                # پردازش جزئیات انبارها
                stock_details = []
                if row[9]:
                    for part in row[9].split(', '):
                        if ':' in part:
                            stock_code, qty = part.split(':')
                            stock_details.append({
                                'stock_code': stock_code,
                                'quantity': float(qty) if qty else 0
                            })
                
                # محاسبه کمبود
                if total_stock > 0:
                    shortage = minimum_amount - total_stock
                else:
                    shortage = total_stock
                
                low_stock_items.append({
                    'code': row[0],
                    'title': row[1] or '',
                    'title_en': row[2] or '',
                    'minimum_amount': minimum_amount,
                    'default_stock_ref': row[4],
                    'unit_ref': row[5],
                    'unit_title': row[6] or '',
                    'default_stock_quantity': float(row[7]) if row[7] else 0,
                    'total_stock_quantity': total_stock,
                    'stock_details': stock_details,
                    'shortage': shortage,
                    'shortage_percent': (shortage / minimum_amount * 100) if minimum_amount > 0 else 0,
                    'status': 'danger' if total_stock == 0 else 'warning'
                })
            
            total_items += 1
        
        db.close()
        
        # مرتب‌سازی بر اساس بیشترین کمبود
        low_stock_items.sort(key=lambda x: x['shortage'], reverse=True)
        
        logger.info(f"Collected {len(low_stock_items)} low stock items out of {total_items} total items")
        
        # ============================================
        # ارسال به سایت seketalamanager.ir
        # ============================================
        payload = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'total_items': total_items,
            'low_stock_count': len(low_stock_items),
            'low_stock_items': low_stock_items,
            'source': 'sepidar_system',
            'report_type': 'low_stock'
        }
        
        target_url = getattr(
            settings, 
            'SEKETALAMANAGER_API_URL', 
            'https://seketalamanager.ir/api/receive-low-stock/'
        )
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {getattr(settings, "SEKETALAMANAGER_API_TOKEN", "")}',
            'X-API-Key': getattr(settings, 'SEKETALAMANAGER_API_KEY', ''),
        }
        
        response = requests.post(
            target_url,
            json=payload,
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            logger.info(
                f"✓ Successfully sent {len(low_stock_items)} low stock items "
                f"to seketalamanager.ir - Status: {response.status_code}"
            )
        else:
            logger.error(
                f"✗ Failed to send to seketalamanager.ir - "
                f"Status: {response.status_code}, Response: {response.text[:500]}"
            )
        
        return {
            'success': True,
            'sent_count': len(low_stock_items),
            'total_items': total_items
        }
        
    except Exception as e:
        logger.error(f"✗ Error in collect_and_send_low_stock_data: {e}", exc_info=True)
        try:
            db.close()
        except:
            pass
        return {'success': False, 'error': str(e)}