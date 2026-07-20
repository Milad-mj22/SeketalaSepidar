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