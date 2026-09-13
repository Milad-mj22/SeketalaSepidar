from django.contrib import admin
from django import forms
from .models import Warehouse, WarehouseRelation


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'number']
    list_filter = ['number']
    search_fields = ['code', 'name', 'number']
    ordering = ['number', 'code']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'code',
                'name',
                'number',
            )
        }),
    )


class WarehouseRelationForm(forms.ModelForm):
    class Meta:
        model = WarehouseRelation
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'order_registration_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        source = cleaned_data.get('source_warehouse')
        destination = cleaned_data.get('destination_warehouse')

        if source and destination and source == destination:
            raise forms.ValidationError("انبار مبدا و مقصد نمی‌توانند یکسان باشند.")

        return cleaned_data


@admin.register(WarehouseRelation)
class WarehouseRelationAdmin(admin.ModelAdmin):
    form = WarehouseRelationForm

    list_display = [
        'relation_name',
        'source_warehouse',
        'destination_warehouse',
        'moin_code',
        'cost_stock',
        'deliverer_ref',
        'created_at',
    ]

    list_filter = [
        'source_warehouse',
        'destination_warehouse',
        'created_at',
    ]

    search_fields = [
        'relation_name',
        'source_warehouse__name',
        'destination_warehouse__name',
        'source_warehouse__code',
        'destination_warehouse__code',
        'source_warehouse__number',
        'destination_warehouse__number',
        'moin_code',
        'cost_stock',
        'deliverer_ref',
        'order_registration_notes',
    ]

    ordering = ['-created_at']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                ('source_warehouse', 'destination_warehouse'),
                'relation_name',
            )
        }),
        ('اطلاعات مالی', {
            'fields': (
                ('moin_code', 'cost_stock'),
            )
        }),
        ('اطلاعات گیرنده', {
            'fields': (
                'deliverer_ref',
            )
        }),
        ('اطلاعات تکمیلی', {
            'fields': (
                'description',
                'order_registration_notes',
            ),
            'classes': ('collapse',),
        }),
        ('زمان ایجاد', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ['created_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('source_warehouse', 'destination_warehouse')