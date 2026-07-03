from .models import Profile

from django.contrib import admin

# Register your models here.
@admin.register(Profile)
class UserAdmin(admin.ModelAdmin):
    list_display = ('phone', 'first_name', 'last_name', 'role','is_active', 'created_at')
    search_fields = ('phone', 'first_name', 'last_name', 'email')
    list_filter = ('role', 'is_active')
    ordering = ('-created_at',)
    # fields = ('phone', 'first_name', 'last_name', 'email', 'role', 'is_active', 'is_staff', 'is_superuser')
    readonly_fields = ('created_at',)

    