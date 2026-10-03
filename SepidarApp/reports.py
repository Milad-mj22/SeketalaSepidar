# SepidarApp/reports.py
"""
گزارش روزانه فعالیت کاربران — بدون ذخیره‌سازی
"""
import logging
from collections import defaultdict
from datetime import datetime
import jdatetime

from django.utils import timezone
from SepidarApp.databaseConnector import db
from SepidarApp.activity_helper import (
    get_users_map,
    get_product_orders,
    get_inventory_deliveries,
    get_inventory_receipts,
    get_accounting_vouchers,
)
from otp_manager.service import send_like2like

logger = logging.getLogger(__name__)


def build_daily_report_text(for_date=None):
    """
    ساخت متن گزارش روزانه از سپیدار
    هیچی ذخیره نمی‌کنه — فقط متن برمی‌گردونه
    
    Returns:
        dict: {
            'success': bool,
            'text': str,       # متن آماده برای پیامک
            'date_shamsi': str,
            'total_activities': int,
            'total_users': int,
            'error': str
        }
    """
    try:
        # تاریخ هدف
        if for_date is None:
            target_date = timezone.now().date()
        else:
            target_date = for_date
        
        logger.info(f"🔄 Building daily report for {target_date}")
        
        # اتصال به سپیدار
        db.connect()
        
        users_map = get_users_map()
        
        # خواندن فعالیت‌های امروز
        orders = get_product_orders(target_date, target_date)
        deliveries = get_inventory_deliveries(target_date, target_date)
        receipts = get_inventory_receipts(target_date, target_date)
        vouchers = get_accounting_vouchers(target_date, target_date)
        
        # جمع‌آوری به ازای هر کاربر
        users_data = defaultdict(lambda: {
            'user_name': '',
            'orders': 0,
            'deliveries': 0,
            'receipts': 0,
            'vouchers': 0,
            'total': 0,
        })
        
        # پردازش هر نوع فعالیت
        for act_list, key in [
            (orders, 'orders'),
            (deliveries, 'deliveries'),
            (receipts, 'receipts'),
            (vouchers, 'vouchers'),
        ]:
            for act in act_list:
                uid = act.get('creator')
                if not uid:
                    continue
                uinfo = users_map.get(uid, {})
                users_data[uid]['user_name'] = uinfo.get('full_name', f'کاربر {uid}')
                users_data[uid][key] += 1
                users_data[uid]['total'] += 1
        
        db.close()
        
        # مرتب‌سازی بر اساس کل فعالیت
        sorted_users = sorted(
            users_data.values(),
            key=lambda x: x['total'],
            reverse=True
        )
        
        # آمار کلی
        total_users = len(sorted_users)
        total_activities = sum(u['total'] for u in sorted_users)
        
        if total_activities == 0:
            # هیچ فعالیتی نبوده
            try:
                shamsi = jdatetime.date.fromgregorian(date=target_date)
                shamsi_str = f"{shamsi.year}/{shamsi.month:02d}/{shamsi.day:02d}"
            except Exception:
                shamsi_str = str(target_date)
            
            return {
                'success': True,
                'text': f"📊 گزارش {shamsi_str}\nهیچ فعالیتی امروز ثبت نشد",
                'date_shamsi': shamsi_str,
                'total_activities': 0,
                'total_users': 0,
            }
        
        # ============================================
        # ساخت متن گزارش
        # ============================================
        try:
            shamsi = jdatetime.date.fromgregorian(date=target_date)
            shamsi_str = f"{shamsi.year}/{shamsi.month:02d}/{shamsi.day:02d}"
        except Exception:
            shamsi_str = str(target_date)
        
        # قالب متن
        lines = []
        lines.append(f"📊 گزارش فعالیت {shamsi_str}")
        lines.append(f"👥 کاربران: {total_users} | 📈 کل: {total_activities}")
        lines.append("─" * 15)
        
        # لیست کاربران
        for i, u in enumerate(sorted_users, 1):
            name = u['user_name']
            # خلاصه: تعداد کل + تفکیک
            parts = []
            if u['orders'] > 0:
                parts.append(f"🏭{u['orders']}")
            if u['deliveries'] > 0:
                parts.append(f"📤{u['deliveries']}")
            if u['receipts'] > 0:
                parts.append(f"📥{u['receipts']}")
            if u['vouchers'] > 0:
                parts.append(f"📑{u['vouchers']}")
            
            lines.append(f"{i}. {name}: {u['total']} ({' '.join(parts)})")
        
        text = "\n".join(lines)
        
        logger.info(f"✅ Report built: {total_users} users, {total_activities} activities")
        
        return {
            'success': True,
            'text': text,
            'date_shamsi': shamsi_str,
            'total_activities': total_activities,
            'total_users': total_users,
        }
        
    except Exception as e:
        logger.error(f"❌ Error building daily report: {e}", exc_info=True)
        try:
            db.close()
        except Exception:
            pass
        return {
            'success': False,
            'error': str(e),
        }


def send_daily_report_sms(for_date=None):
    """
    ساخت و ارسال پیامک گزارش روزانه
    """
    from otp_manager.models import (
        SMS_Template, SMS_Recievers, SMSServiceTemplate_Enum
    )
    from otp_manager.service import send_sms
    
    try:
        # 1. ساخت متن
        report = build_daily_report_text(for_date)
        
        if not report.get('success'):
            logger.error(f"❌ Failed to build report: {report.get('error')}")
            return report
        
        report_text = report.get('text', '')
        
        if not report_text:
            return {'success': False, 'error': 'Empty text'}
        
        # 2. دریافت قالب پیامک
        sms_template = SMS_Template.objects.filter(
            name=SMSServiceTemplate_Enum.ACTIVITY  # ← یا قالب خاص خودت
        ).first()
        
        if not sms_template:
            logger.warning("⚠️ SMS template not found")
            return {'success': False, 'error': 'Template not found'}
        
        # 3. دریافت گیرندگان
        sms_receivers = SMS_Recievers.objects.filter(template=sms_template)
        
        if not sms_receivers.exists():
            logger.warning("⚠️ No receivers found")
            return {'success': False, 'error': 'No receivers'}
        
        # 4. ارسال به همه گیرندگان
        sent_count = 0
        errors = []

        phones = []
        texts = []


        
        for rec in sms_receivers:
            phone = rec.persons.phone
            try:
                phones.append(phone)
                texts.append(report_text)                    
            except Exception as e:
                errors.append(f"{phone}: {str(e)}")
                logger.error(f"❌ SMS error for {phone}: {e}")

        ret= send_like2like(template_obj=sms_template,phone_numbers=phones,text=texts)
        print(ret)
        return {
            'success': sent_count > 0,
            'sent_count': sent_count,
            'total_receivers': sms_receivers.count(),
            'report_text': report_text,
            'date_shamsi': report.get('date_shamsi'),
            'total_activities': report.get('total_activities'),
            'errors': errors,
        }
        
    except Exception as e:
        logger.error(f"❌ Error sending daily report SMS: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}