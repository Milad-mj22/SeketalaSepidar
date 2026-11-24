import jdatetime

def persian_to_gregorian(persian_date_str,ret_full = True):
    # Split the date
    parts = persian_date_str.split('/')
    year = int(parts[0])
    month = int(parts[1])
    day = int(parts[2])
    
    # Create Jalali date
    jalali_date = jdatetime.date(year, month, day)
    
    # Convert to Gregorian
    gregorian_date = jalali_date.togregorian()
    if ret_full:
        return gregorian_date
    return gregorian_date.strftime('%Y-%m-%d')





def get_creator_sepidar(request=None):
    """
    دریافت کد سپیدار کاربر فعلی
    - اگه کاربر لاگین باشه و sepidar_code داشته باشه → همون
    - وگرنه → مقدار پیش‌فرض از settings
    """
    from SekeSepidar.settings import CREATOR_SEPIDAR as DEFAULT_CREATOR
    
    if request is None:
        return DEFAULT_CREATOR
    
    try:
        if request.user.is_authenticated:
            profile = request.user.profile
            if profile.sepidar_code:
                return profile.sepidar_code
    except Exception:
        pass
    
    return DEFAULT_CREATOR







# SepidarApp/utils.py
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """دریافت IP کاربر"""
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    except Exception:
        return None


def get_user_display_name(user):
    """دریافت نام نمایشی کاربر"""
    try:
        if hasattr(user, 'profile') and user.profile:
            first = user.profile.first_name or ''
            last = user.profile.last_name or ''
            name = f"{first} {last}".strip()
            if name:
                return name
        return user.get_full_name() or user.username
    except Exception:
        return str(user)


def log_activity(
    request,
    action_type='formula_submit',
    relation=None,
    receipt_number=None,
    description='',
    details=None,
    total_formulas=0,
    total_items=0,
    total_temp_items=0,
):
    """
    ثبت یه رکورد فعالیت جدید
    
    Returns:
        ActivityLog instance or None
    """
    from SepidarApp.models import ActivityLog
    
    try:
        user = request.user if request and hasattr(request, 'user') and request.user.is_authenticated else None
        
        activity = ActivityLog.objects.create(
            user=user,
            user_display_name=get_user_display_name(user) if user else 'ناشناس',
            action_type=action_type,
            relation=relation,
            relation_name=relation.relation_name if relation else '',
            receipt_number=receipt_number,
            description=description,
            details=details,
            total_formulas=total_formulas,
            total_items=total_items,
            total_temp_items=total_temp_items,
            ip_address=get_client_ip(request) if request else None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else '',
        )
        
        logger.info(f"✅ Activity logged: {activity}")
        return activity
        
    except Exception as e:
        logger.error(f"❌ Error logging activity: {e}", exc_info=True)
        return None












if __name__=='__main__':
    # Example
    persian_date = '۱۴۰۵/۰۵/۰۲'
    gregorian_date = persian_to_gregorian(persian_date)
    print(gregorian_date)  # Output: 2026-07-24
