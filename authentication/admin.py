from .models import Profile

from django.contrib import admin


import logging
logger = logging.getLogger(__name__)

from django.contrib import admin, messages
from .models import Profile
from .sepidar_helper import get_sepidar_code_from_db


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'phone', 'first_name', 'last_name','sepidar_username', 'role',
        'sepidar_code', 'is_active', 'created_at'
    )
    search_fields = ('phone', 'first_name', 'last_name', 'email')
    list_filter = ('role', 'is_active')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    # فیلد sepidar_code رو توی فرم نشون بده
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('اطلاعات امنیتی', {
            'fields': ('password_hash', 'role', 'is_active', 'avatar')
        }),
        ('اطلاعات سپیدار', {
            'fields': ('sepidar_username','sepidar_code',),
            'description': 'کد کاربر در نرم‌افزار سپیدار. با Action «دریافت کد سپیدار» قابل به‌روزرسانی است.'
        }),
        ('متادیتا', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    # ============================================
    # Actions
    # ============================================
    actions = ['fetch_sepidar_code_action']

    @admin.action(description='🔄 دریافت کد سپیدار از دیتابیس')
    def fetch_sepidar_code_action(self, request, queryset):
        """
        برای هر کاربر انتخاب‌شده، کد سپیدار رو از دیتابیس سپیدار می‌گیره
        و توی فیلد sepidar_code ذخیره می‌کنه.
        """
        success_count = 0
        fail_count = 0
        errors = []

        for profile in queryset:
            sepidar_username = profile.sepidar_username 


            if not sepidar_username :
                fail_count += 1
                errors.append(f"❌ {profile} - نام کاربری خالی است")
                continue

            result = get_sepidar_code_from_db(sepidar_username)

            if result['success']:
                profile.sepidar_code = result['user_id']
                profile.save(update_fields=['sepidar_code'])
                success_count += 1
                self.message_user(
                    request,
                    f"✅ {profile}: {result['message']}",
                    level=messages.SUCCESS
                )
            else:
                fail_count += 1
                errors.append(f"❌ {profile}: {result['message']}")
                self.message_user(
                    request,
                    f"❌ {profile}: {result['message']}",
                    level=messages.ERROR
                )

        # پیام خلاصه
        self.message_user(
            request,
            f"📊 نتیجه: {success_count} موفق، {fail_count} ناموفق",
            level=messages.INFO
        )

        if errors:
            self.message_user(
                request,
                "جزئیات خطاها در لاگ سرور ثبت شد.",
                level=messages.WARNING
            )
            for err in errors:
                logger.warning(err)