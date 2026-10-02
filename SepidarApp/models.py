from django.db import models

# Create your models here.
class Warehouse(models.Model):
    """
    مدل انبار با کد، نام و شماره دلخواه
    """
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="کد انبار",
        help_text="کد منحصر‌به‌فرد انبار"
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name="نام انبار",
        help_text="نام نمایشی انبار"
    )
    
    # شماره دلخواه برای انبار (مثبت و صحیح)
    number = models.PositiveIntegerField(
        verbose_name="شماره انبار",
        help_text="یک عدد دلخواه برای انبار وارد کنید (مثبت)",
        default=1
    )

    class Meta:
            verbose_name = "انبار"
            verbose_name_plural = "انبارها"
            ordering = ['number', 'code']
        
    def __str__(self):
        return f"{self.code} - {self.name} (شماره {self.number})"






class WarehouseRelation(models.Model):
    """
    مدل رابطه بین دو انبار با نام دلخواه
    """
    # رابطه با انبار مبدا
    source_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='source_relations',
        verbose_name="انبار مبدا"
    )
    
    # رابطه با انبار مقصد
    destination_warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='destination_relations',
        verbose_name="انبار مقصد"
    )
    
    # نام رابطه (توسط کاربر وارد می‌شود)
    relation_name = models.CharField(
        max_length=200,
        verbose_name="نام رابطه",
        help_text="نامی که به این رابطه اختصاص می‌دهید"
    )
    
    # توضیحات اضافی (اختیاری)
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="توضیحات"
    )

    moin_code = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="کد معین",
        help_text="کد معین مرتبط با این رابطه"
    )

    cost_stock = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="کد مرکز هزینه",
        help_text="کد مرکز هزینه مرتبط با این رابطه"
    )

    deliverer_ref =  models.IntegerField(
        null=True,
        blank=True,
        verbose_name="کد گیرنده",
        help_text="کد گیزنده با این رابطه"
    )


    order_registration_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="توضیحات ثبت سفارش",
        help_text="توضیحات یا نکات مربوط به ثبت سفارش برای این رابطه"
    )


    # تاریخ ایجاد
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    
    class Meta:
        verbose_name = "رابطه انبار"
        verbose_name_plural = "روابط انبارها"
        ordering = ['-created_at']
        # اطمینان از منحصر‌به‌فرد بودن ترکیب مبدا و مقصد
        unique_together = [['source_warehouse', 'destination_warehouse']]
    
    def __str__(self):
        return f"{self.relation_name} - {self.source_warehouse} → {self.destination_warehouse}"
    
    def clean(self):
        """
        اعتبارسنجی اضافی: جلوگیری از ایجاد رابطه با خودش
        """
        from django.core.exceptions import ValidationError
        if self.source_warehouse == self.destination_warehouse:
            raise ValidationError("انبار مبدا و مقصد نمی‌توانند یکسان باشند.")
    
    def save(self, *args, **kwargs):
        # اجرای اعتبارسنجی قبل از ذخیره
        super().save(*args, **kwargs)







# SepidarApp/models.py

class RelationFormula(models.Model):
    """
    فرمول‌های مجاز برای یک رابطه انبار
    هر رابطه می‌تونه چند فرمول داشته باشه و هر فرمول می‌تونه توی چند رابطه باشه
    """
    relation = models.ForeignKey(
        WarehouseRelation,
        on_delete=models.CASCADE,
        related_name='formula_relations',
        verbose_name="رابطه انبار"
    )
    
    # شناسه فرمول در سپیدار
    formula_id = models.IntegerField(
        verbose_name="شناسه فرمول (سپیدار)",
        db_index=True
    )
    
    # اطلاعات cache شده از سپیدار (برای جلوگیری از کوئری مکرر)
    formula_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="کد فرمول"
    )
    formula_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="عنوان فرمول"
    )
    formula_item_ref = models.IntegerField(
        null=True, blank=True,
        verbose_name="مرجع محصول"
    )
    formula_product_name = models.CharField(
        max_length=255, blank=True,
        verbose_name="نام محصول"
    )
    
    # ✅ علامت حذف (اگه توی سپیدار پاک شد)
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="حذف شده از سپیدار"
    )
    deleted_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name="تاریخ حذف"
    )
    
    # ✅ یادداشت
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="یادداشت",
        help_text="یادداشت مخصوص این رابطه-فرمول"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    
    class Meta:
        verbose_name = "فرمول رابطه"
        verbose_name_plural = "فرمول‌های روابط"
        ordering = ['formula_code']
        unique_together = [['relation', 'formula_id']]
        indexes = [
            models.Index(fields=['relation', 'formula_id']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        status = "🚫" if self.is_deleted else "✅"
        return f"{status} {self.formula_code} - {self.formula_title}"
    
    @property
    def is_available(self):
        """آیا این فرمول هنوز توی سپیدار موجوده؟"""
        return not self.is_deleted





# SepidarApp/models.py

class ActivityLog(models.Model):
    """
    ثبت تاریخچه فعالیت‌های کاربران
    هر بار که کاربر یک عملیات ثبت موفق انجام می‌ده، یک رکورد اضافه می‌شود
    """
    
    ACTION_CHOICES = [
        ('formula_submit', 'ثبت فرمول‌ها'),
        ('formula_submit_failed', 'ثبت فرمول‌ها (ناموفق)'),
        ('item_add_temp', 'افزودن ماده موقت'),
    ]
    
    # کاربر
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='activity_logs',
        verbose_name="کاربر"
    )
    user_display_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="نام نمایشی کاربر",
        help_text="نام کاربر در زمان ثبت (کش شده)"
    )
    
    # نوع فعالیت
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        default='formula_submit',
        verbose_name="نوع فعالیت"
    )
    
    # اطلاعات رابطه
    relation = models.ForeignKey(
        WarehouseRelation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='activity_logs',
        verbose_name="رابطه انبار"
    )
    relation_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="نام رابطه (کش شده)"
    )
    
    # ✅ شماره رسید برگشتی
    receipt_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="شماره رسید",
        help_text="شماره رسید/سفارش تولیدی که ساخته شده"
    )
    
    # اطلاعات تکمیلی
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="توضیحات"
    )
    details = models.JSONField(
        null=True, blank=True,
        verbose_name="جزئیات",
        help_text="اطلاعات کامل ثبت شده به صورت JSON"
    )
    
    # آمار خلاصه
    total_formulas = models.IntegerField(
        default=0,
        verbose_name="تعداد فرمول‌ها"
    )
    total_items = models.IntegerField(
        default=0,
        verbose_name="تعداد کل مواد"
    )
    total_temp_items = models.IntegerField(
        default=0,
        verbose_name="تعداد مواد موقت"
    )
    
    # اطلاعات فنی
    ip_address = models.GenericIPAddressField(
        null=True, blank=True,
        verbose_name="آدرس IP"
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="User Agent"
    )
    
    # زمان
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ثبت",
        db_index=True
    )
    
    class Meta:
        verbose_name = "تاریخچه فعالیت"
        verbose_name_plural = "تاریخچه فعالیت‌ها"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user_display_name or 'ناشناس'} - {self.get_action_type_display()} - {self.created_at.strftime('%Y/%m/%d %H:%M')}"