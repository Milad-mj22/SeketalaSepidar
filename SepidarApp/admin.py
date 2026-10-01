# SepidarApp/admin.py
import logging

from django.contrib import admin
from .models import Warehouse, WarehouseRelation, RelationFormula
from .forms import WarehouseRelationAdminForm


# ============================================================
# Warehouse Admin
# ============================================================
@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'number']
    list_filter = ['number']
    search_fields = ['code', 'name', 'number']
    ordering = ['number', 'code']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('code', 'name', 'number')
        }),
    )


    
logger = logging.getLogger(__name__)

@admin.register(WarehouseRelation)
class WarehouseRelationAdmin(admin.ModelAdmin):
    form = WarehouseRelationAdminForm

    list_display = [
        'relation_name',
        'source_warehouse',
        'destination_warehouse',
        'formula_count',
        'moin_code',
        'cost_stock',
        'deliverer_ref',
        'created_at',
    ]
    list_filter = ['source_warehouse', 'destination_warehouse', 'created_at']
    search_fields = [
        'relation_name',
        'source_warehouse__name',
        'destination_warehouse__name',
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (('source_warehouse', 'destination_warehouse'), 'relation_name')
        }),
        ('اطلاعات مالی', {
            'fields': (('moin_code', 'cost_stock'),)
        }),
        ('اطلاعات گیرنده', {
            'fields': ('deliverer_ref',)
        }),
        ('🎯 فرمول‌های مجاز', {
            'fields': ('formula_ids',),
            'description': 'فرمول‌هایی که در این رابطه نمایش داده می‌شوند را انتخاب کنید.'
        }),
        ('اطلاعات تکمیلی', {
            'fields': ('description', 'order_registration_notes'),
            'classes': ('collapse',),
        }),
        ('زمان ایجاد', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ['created_at']

    def formula_count(self, obj):
        total = obj.formula_relations.count()
        deleted = obj.formula_relations.filter(is_deleted=True).count()
        active = total - deleted
        if deleted > 0:
            return f"{active} فعال / {deleted} حذف‌شده"
        return f"{active} فرمول"
    formula_count.short_description = "تعداد فرمول"

    # ✅ اینجا فرمول‌ها رو ذخیره می‌کنیم
    def save_model(self, request, obj, form, change):
        logger.warning(f"🚀 admin.save_model() called, pk={obj.pk}")
        
        # اول instance رو ذخیره کن (جنگو خودش)
        super().save_model(request, obj, form, change)
        
        logger.warning(f"✅ super().save_model() OK, pk={obj.pk}")
        
        # حالا فرمول‌ها رو ذخیره کن
        pending_ids = getattr(obj, '_pending_formula_ids', None)
        logger.warning(f"📦 pending_ids from obj: {pending_ids}")
        
        if pending_ids is not None:
            form.save_formulas(obj, pending_ids)