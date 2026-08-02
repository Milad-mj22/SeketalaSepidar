# stockManager/models.py

from django.db import models
from django.contrib.auth.models import User

# ... مدل‌های دیگر شما ...

class MaterialAdjustment(models.Model):
    """تنظیمات مواد اولیه"""
    item_code = models.CharField(max_length=50, unique=True, verbose_name="کد ماده")
    item_name = models.CharField(max_length=200, verbose_name="نام ماده")
    adjustment_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        verbose_name="درصد تنظیم"
    )
    send_sms = models.BooleanField(default=False, verbose_name="ارسال پیامک")
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="ثبت کننده")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    last_modified = models.DateTimeField(auto_now=True, verbose_name="تاریخ ویرایش")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    
    class Meta:
        verbose_name = "تنظیم مواد"
        verbose_name_plural = "تنظیمات مواد"
        ordering = ['item_code']
    
    def __str__(self):
        return f"{self.item_code} - {self.item_name} ({self.adjustment_percent}%)"


# ============================================
# ✅ اضافه کردن این مدل جدید
# ============================================
class DailyJobLog(models.Model):
    """لاگ اجرای وظایف روزانه"""
    
    STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('running', 'در حال اجرا'),
        ('success', 'موفق'),
        ('failed', 'ناموفق'),
    ]
    
    executed_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان اجرا")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="وضعیت"
    )
    message = models.TextField(blank=True, verbose_name="پیام")
    result = models.JSONField(null=True, blank=True, verbose_name="نتیجه")
    duration = models.FloatField(null=True, blank=True, verbose_name="مدت زمان اجرا (ثانیه)")
    
    class Meta:
        ordering = ['-executed_at']
        verbose_name = "لاگ وظیفه روزانه"
        verbose_name_plural = "لاگ‌های وظایف روزانه"
    
    def __str__(self):
        return f"{self.executed_at} - {self.status}"


class MaterialAdjustmentHistory(models.Model):
    """تاریخچه تنظیمات مواد (اختیاری)"""
    item_code = models.CharField(max_length=50, verbose_name="کد ماده")
    item_name = models.CharField(max_length=200, verbose_name="نام ماده")
    adjustment_percent = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="درصد تنظیم")
    old_quantity = models.DecimalField(max_digits=19, decimal_places=4, verbose_name="موجودی قبلی")
    new_quantity = models.DecimalField(max_digits=19, decimal_places=4, verbose_name="موجودی جدید")
    send_sms = models.BooleanField(default=False, verbose_name="ارسال پیامک")
    processed_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان پردازش")
    
    class Meta:
        ordering = ['-processed_at']
        verbose_name = "تاریخچه تنظیمات"
        verbose_name_plural = "تاریخچه تنظیمات مواد"
    
    def __str__(self):
        return f"{self.item_code} - {self.processed_at}"