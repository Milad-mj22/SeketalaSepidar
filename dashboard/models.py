from django.db import models

# Create your models here.


from django.db import models
from django.contrib.auth.models import User

class Page(models.Model):
    name = models.CharField(max_length=255, unique=True)
    label = models.CharField(max_length=255)
    icon = models.TextField(blank=True, null=True)  # برای ذخیره HTML
    type = models.CharField(
        max_length=10,
        choices=[
            ('item', 'Item'),
            ('tree', 'Tree')
        ],
        default='item'
    )
    link = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.IntegerField(default=0)  # برای اولویت‌بندی

    def __str__(self):
        return f"{self.name} == {self.link} , order : {self.order}"
    


    def get_page_list():
        pages = Page.objects.order_by('order')
        result = []

        for page in pages:
            page_data = {
                "name": page.name,
                "label": page.label,
                "icon": page.icon,
                "type": page.type,
                "link": page.link,
            }

            if page.type == "tree" and page.subpages:
                subs = []
                for sub in page.subpages.order_by('order'):
                    subs.append({
                        "name": sub.name,
                        "label": sub.label,
                        "icon": sub.icon,
                        "type": sub.type,
                        "link": sub.link,
                    })
                page_data["subs"] = subs

            result.append(page_data)

        return result


class SubPage(models.Model):
    parent_page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='subpages')
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    icon = models.TextField(blank=True, null=True)
    type = models.CharField(
        max_length=10,
        choices=[
            ('item', 'Item'),
            ('tree', 'Tree')
        ],
        default='item'
    )
    link = models.CharField(max_length=255, blank=True, null=True)
    order = models.IntegerField(default=0)  # برای اولویت‌بندی

    def __str__(self):
        return f"{self.parent_page.name} -> {self.name} == {self.link} , order : {self.order}"






from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class BaseSettings(models.Model):
    """
    تنظیمات اصلی نرم‌افزار - فقط یک سطر وجود خواهد داشت
    """
    
    # اطلاعات عمومی
    name = models.CharField(
        max_length=255,
        default='سیستم مدیریت دیتاست',
        verbose_name='نام اپلیکیشن'
    )
    name_en = models.CharField(
        max_length=255,
        default='Dataset Management System',
        verbose_name='نام اپلیکیشن (انگلیسی)'
    )
    logo = models.ImageField(
        upload_to='assets/logo/',
        blank=True,
        null=True,
        verbose_name='لوگوی اپلیکیشن'
    )

    sidebar_logo = models.ImageField(
        upload_to='assets/sidebar_logo/',
        blank=True,
        null=True,
        verbose_name='لوگوی سایدبار'
    )

    sidebar_title = models.CharField(
        max_length=255,
        default='test',
    )
    favicon = models.ImageField(
        upload_to='assets/favicon/',
        blank=True,
        null=True,
        verbose_name='فاویکون'
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات اپلیکیشن'
    )


    base_dataset_dir = models.CharField(
        max_length=1000,
        blank=True,
        default='datasets',
        verbose_name='محل ذخیره سازی دیتاست ها'
    )

    base_ai_models_dir = models.CharField(
        max_length=1000,
        blank=True,
        default='ai_models',
        verbose_name='محل ذخیره سازی مدل ها'
    )
    
    # محدودیت‌ها
    max_datasets = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        verbose_name='حداکثر تعداد دیتاست'
    )
    max_users = models.IntegerField(
        default=100,
        validators=[MinValueValidator(1)],
        verbose_name='حداکثر تعداد کاربران'
    )
    max_classes_per_dataset = models.IntegerField(
        default=50,
        validators=[MinValueValidator(1)],
        verbose_name='حداکثر تعداد کلاس در هر دیتاست'
    )
    max_images_per_dataset = models.IntegerField(
        default=10000,
        validators=[MinValueValidator(1)],
        verbose_name='حداکثر تعداد تصویر در هر دیتاست'
    )
    max_image_size = models.IntegerField(
        default=10,  # MB
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        verbose_name='حداکثر حجم تصویر (مگابایت)'
    )
    
    # تنظیمات ایمیل
    email_host = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='سرور ایمیل'
    )
    email_port = models.IntegerField(
        default=587,
        blank=True,
        verbose_name='پورت ایمیل'
    )
    email_username = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='نام کاربری ایمیل'
    )
    email_password = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='رمز ایمیل'
    )
    email_use_tls = models.BooleanField(
        default=True,
        verbose_name='استفاده از TLS'
    )
    email_from = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='ایمیل فرستنده'
    )
    
    # تنظیمات ظاهر
    primary_color = models.CharField(
        max_length=7,
        default='#3498db',
        verbose_name='رنگ اصلی'
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#2ecc71',
        verbose_name='رنگ ثانویه'
    )
    theme_mode = models.CharField(
        max_length=10,
        choices=[
            ('light', 'روشن'),
            ('dark', 'تاریک'),
            ('auto', 'خودکار'),
        ],
        default='light',
        verbose_name='حالت ظاهری'
    )


    
    # تنظیمات امنیتی
    session_timeout = models.IntegerField(
        default=30,  # دقیقه
        verbose_name='زمان انقضای جلسه (دقیقه)'
    )
    max_login_attempts = models.IntegerField(
        default=5,
        verbose_name='حداکثر تلاش برای ورود'
    )
    password_min_length = models.IntegerField(
        default=8,
        verbose_name='حداقل طول رمز عبور'
    )
    require_email_verification = models.BooleanField(
        default=False,
        verbose_name='نیاز به تایید ایمیل'
    )
    
    # تنظیمات سیستم
    is_maintenance_mode = models.BooleanField(
        default=False,
        verbose_name='حالت تعمیرات'
    )
    maintenance_message = models.TextField(
        blank=True,
        verbose_name='پیام تعمیرات'
    )
    allow_registration = models.BooleanField(
        default=True,
        verbose_name='اجازه ثبت‌نام'
    )
    
    # متادیتا
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ایجاد'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاریخ بروزرسانی'
    )

    class Meta:
        verbose_name = 'تنظیمات اپلیکیشن'
        verbose_name_plural = 'تنظیمات اپلیکیشن'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # اطمینان از وجود فقط یک سطر
        self.__class__.objects.exclude(pk=self.pk).delete()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """دریافت تنظیمات (یا ایجاد پیش‌فرض)"""
        settings, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'name': 'سیستم مدیریت دیتاست',
                'name_en': 'Dataset Management System',
            }
        )
        return settings