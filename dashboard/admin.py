
from django.contrib import admin
from .models import Page, SubPage

class SubPageInline(admin.TabularInline):
    model = SubPage
    fields = ('name', 'label', 'order')
    list_display = ('name', 'order')
    fk_name = 'parent_page'  # Important:  Specifies the ForeignKey relationship

class PageAdmin(admin.ModelAdmin):
    list_display = ('name', 'label', 'order', 'type')
    list_editable = ('order',)
    ordering = ('order',)
    inlines = [SubPageInline]

admin.site.register(Page, PageAdmin)
admin.site.register(SubPage)



# admin.py
from django.contrib import admin
from .models import BaseSettings


@admin.register(BaseSettings)
class BaseSettingsAdmin(admin.ModelAdmin):
    list_display = ['name', 'name_en', 'is_maintenance_mode', 'updated_at']
    list_editable = ['is_maintenance_mode']
    
    fieldsets = (
        ('اطلاعات عمومی', {
            'fields': ('name', 'name_en','sidebar_title','sidebar_logo', 'logo', 'favicon', 'description')
        }),
        ('محدودیت‌ها', {
            'fields': ('max_datasets', 'max_users', 'max_classes_per_dataset', 
                      'max_images_per_dataset', 'max_image_size')
        }),
        ('ایمیل', {
            'fields': ('email_host', 'email_port', 'email_username', 
                      'email_password', 'email_use_tls', 'email_from'),
            'classes': ('collapse',)
        }),
        ('ظاهر', {
            'fields': ('primary_color', 'secondary_color', 'theme_mode')
        }),
        ('امنیت', {
            'fields': ('session_timeout', 'max_login_attempts', 
                      'password_min_length', 'require_email_verification')
        }),
        ('سیستم', {
            'fields': ('base_dataset_dir','is_maintenance_mode', 'maintenance_message', 'allow_registration')
        }),
    )
    
    def has_add_permission(self, request, obj=None):
        """جلوگیری از افزودن"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """جلوگیری از حذف"""
        return True
    
    def has_change_permission(self, request, obj=None):
        """اجازه ویرایش"""
        return True
    
    def has_view_permission(self, request, obj=None):
        """اجازه مشاهده"""
        return True