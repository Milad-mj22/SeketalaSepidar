# SepidarApp/admin.py
import logging
from django.utils.html import format_html
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










# SepidarApp/admin.py
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = [
        'created_at',
        'user_display_name',
        'action_type_badge',
        'relation_name',
        'receipt_number',
        'total_formulas',
        'total_items',
        'total_temp_items',
    ]
    list_filter = ['action_type', 'created_at', 'user']
    search_fields = [
        'user_display_name',
        'receipt_number',
        'relation_name',
        'description',
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    readonly_fields = [
        'user', 'user_display_name', 'action_type',
        'relation', 'relation_name', 'receipt_number',
        'description', 'details',
        'total_formulas', 'total_items', 'total_temp_items',
        'ip_address', 'user_agent', 'created_at',
    ]
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'user_display_name', 'ip_address', 'user_agent')
        }),
        ('اطلاعات فعالیت', {
            'fields': ('action_type', 'relation', 'relation_name', 'receipt_number', 'created_at')
        }),
        ('آمار', {
            'fields': ('total_formulas', 'total_items', 'total_temp_items')
        }),
        ('توضیحات و جزئیات', {
            'fields': ('description', 'details'),
            'classes': ('collapse',)
        }),
    )
    
    def action_type_badge(self, obj):
        colors = {
            'formula_submit': '#22c55e',
            'formula_submit_failed': '#ef4444',
            'item_add_temp': '#f59e0b',
        }
        color = colors.get(obj.action_type, '#64748b')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; '
            'border-radius: 10px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_action_type_display()
        )
    action_type_badge.short_description = "نوع فعالیت"
    
    def has_add_permission(self, request):
        # فقط از طریق سیستم ثبت می‌شه
        return False
    
    def has_change_permission(self, request, obj=None):
        # فقط خواندنی
        return False