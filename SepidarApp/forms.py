# SepidarApp/forms.py
from django import forms
from django.utils.safestring import mark_safe
from django.db import transaction
import logging

from .models import WarehouseRelation, RelationFormula
from .formula_helper import get_all_formulas_from_sepidar

logger = logging.getLogger(__name__)


class FormulaSelectorWidget(forms.Widget):
    """ویجت سفارشی برای انتخاب فرمول‌ها با چک‌باکس و جستجو"""

    def render(self, name, value, attrs=None, renderer=None):
        # value = لیست IDها
        selected_ids = set()
        if value:
            if isinstance(value, str):
                selected_ids = {int(x) for x in value.split(',') if x.strip().isdigit()}
            elif isinstance(value, (list, tuple, set)):
                for v in value:
                    try:
                        selected_ids.add(int(v))
                    except (ValueError, TypeError):
                        pass

        # گرفتن فرمول‌ها
        try:
            from SepidarApp.databaseConnector import db
            db.connect()
            all_formulas = get_all_formulas_from_sepidar()
        except Exception as e:
            logger.error(f"Error fetching formulas: {e}")
            all_formulas = []

        html = '''
        <div class="formula-selector-widget" dir="rtl">
            <style>
                .formula-selector-widget {
                    border: 2px solid #e2e8f0;
                    border-radius: 10px;
                    background: white;
                    font-family: 'Segoe UI', Tahoma, sans-serif;
                }
                .fsw-toolbar {
                    padding: 12px 16px;
                    background: #f8fafc;
                    border-bottom: 1px solid #e2e8f0;
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                    align-items: center;
                }
                .fsw-search {
                    flex: 1;
                    min-width: 200px;
                    padding: 8px 14px;
                    border: 2px solid #e2e8f0;
                    border-radius: 8px;
                    font-size: 13px;
                    font-family: inherit;
                }
                .fsw-search:focus {
                    outline: none;
                    border-color: #4f46e5;
                    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
                }
                .fsw-btn {
                    padding: 8px 14px;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: 600;
                    cursor: pointer;
                    font-family: inherit;
                    color: white;
                }
                .fsw-btn-primary { background: #4f46e5; }
                .fsw-btn-warning { background: #f59e0b; }
                .fsw-btn-secondary { background: #64748b; }
                .fsw-list {
                    max-height: 500px;
                    overflow-y: auto;
                    padding: 8px;
                }
                .fsw-item {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    padding: 10px 12px;
                    border-radius: 8px;
                    border: 1px solid transparent;
                    transition: background 0.15s;
                    cursor: pointer;
                }
                .fsw-item:hover {
                    background: #f8fafc;
                    border-color: #e2e8f0;
                }
                .fsw-item.checked {
                    background: #f0fdf4;
                    border-color: #86efac;
                }
                .fsw-item.hidden {
                    display: none;
                }
                .fsw-item input[type="checkbox"] {
                    width: 18px;
                    height: 18px;
                    accent-color: #4f46e5;
                    cursor: pointer;
                    flex-shrink: 0;
                }
                .fsw-code {
                    background: #e0e7ff;
                    color: #1e293b;
                    padding: 3px 10px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: 700;
                    flex-shrink: 0;
                    min-width: 60px;
                    text-align: center;
                }
                .fsw-title {
                    flex: 1;
                    color: #334155;
                    font-size: 13px;
                    font-weight: 500;
                }
                .fsw-product {
                    color: #64748b;
                    font-size: 11px;
                    flex-shrink: 0;
                }
                .fsw-badge {
                    padding: 2px 8px;
                    border-radius: 10px;
                    font-size: 10px;
                    font-weight: 600;
                }
                .fsw-badge-active { background: #dcfce7; color: #166534; }
                .fsw-badge-inactive { background: #f3f4f6; color: #6b7280; }
                .fsw-counter {
                    padding: 10px 16px;
                    background: #f8fafc;
                    border-top: 1px solid #e2e8f0;
                    font-size: 13px;
                    color: #334155;
                    font-weight: 600;
                    display: flex;
                    justify-content: space-between;
                }
                .fsw-counter .num {
                    background: #4f46e5;
                    color: white;
                    padding: 3px 10px;
                    border-radius: 10px;
                    font-size: 12px;
                }
                .fsw-empty {
                    text-align: center;
                    padding: 40px 20px;
                    color: #94a3b8;
                }
            </style>

            <div class="fsw-toolbar">
                <input type="text" class="fsw-search" placeholder="🔍 جستجو..."
                       oninput="fswSearch(this)">
                <button type="button" class="fsw-btn fsw-btn-primary" onclick="fswSelectAll(this)">✅ همه</button>
                <button type="button" class="fsw-btn fsw-btn-warning" onclick="fswSelectActive(this)">🟢 فعال</button>
                <button type="button" class="fsw-btn fsw-btn-secondary" onclick="fswDeselectAll(this)">❌ حذف</button>
            </div>

            <div class="fsw-list">
        '''

        if not all_formulas:
            html += '''
                <div class="fsw-empty">
                    <div style="font-size: 40px; margin-bottom: 8px;">📭</div>
                    <div style="font-weight: 600;">هیچ فرمولی یافت نشد</div>
                </div>
            '''
        else:
            for f in all_formulas:
                is_checked = f['id'] in selected_ids
                is_active = f['is_active']
                search_text = f"{f['code']} {f['title']} {f['product_name']}".lower()

                checked_attr = 'checked' if is_checked else ''
                checked_class = 'checked' if is_checked else ''
                badge = (
                    '<span class="fsw-badge fsw-badge-active">فعال</span>' if is_active
                    else '<span class="fsw-badge fsw-badge-inactive">غیرفعال</span>'
                )

                html += f'''
                <label class="fsw-item {checked_class}"
                       data-search="{search_text}"
                       data-active="{str(is_active).lower()}">
                    <input type="checkbox"
                           name="{name}"
                           value="{f['id']}"
                           {checked_attr}
                           onchange="fswOnChange(this)">
                    <span class="fsw-code">{f['code']}</span>
                    <span class="fsw-title">{f['title']}</span>
                    <span class="fsw-product">{f['product_name']}</span>
                    {badge}
                </label>
                '''

        html += f'''
            </div>

            <div class="fsw-counter">
                <span>انتخاب شده: <span class="num fsw-selected-count">0</span></span>
                <span style="color:#64748b; font-weight:500; font-size:12px;">از <span class="fsw-total-count">0</span> فرمول</span>
            </div>
        </div>

        <script>
            function fswSearch(input) {{
                const term = input.value.toLowerCase().trim();
                const container = input.closest('.formula-selector-widget');
                const items = container.querySelectorAll('.fsw-item');
                items.forEach(item => {{
                    const text = item.dataset.search;
                    const matches = !term || text.includes(term);
                    item.classList.toggle('hidden', !matches);
                }});
            }}

            function fswOnChange(checkbox) {{
                const item = checkbox.closest('.fsw-item');
                item.classList.toggle('checked', checkbox.checked);
                fswUpdateCounter(checkbox.closest('.formula-selector-widget'));
            }}

            function fswSelectAll(btn) {{
                const container = btn.closest('.formula-selector-widget');
                container.querySelectorAll('.fsw-item:not(.hidden)').forEach(item => {{
                    const cb = item.querySelector('input[type="checkbox"]');
                    cb.checked = true;
                    item.classList.add('checked');
                }});
                fswUpdateCounter(container);
            }}

            function fswSelectActive(btn) {{
                const container = btn.closest('.formula-selector-widget');
                container.querySelectorAll('.fsw-item:not(.hidden)').forEach(item => {{
                    const cb = item.querySelector('input[type="checkbox"]');
                    const isActive = item.dataset.active === 'true';
                    cb.checked = isActive;
                    item.classList.toggle('checked', isActive);
                }});
                fswUpdateCounter(container);
            }}

            function fswDeselectAll(btn) {{
                const container = btn.closest('.formula-selector-widget');
                container.querySelectorAll('.fsw-item').forEach(item => {{
                    const cb = item.querySelector('input[type="checkbox"]');
                    cb.checked = false;
                    item.classList.remove('checked');
                }});
                fswUpdateCounter(container);
            }}

            function fswUpdateCounter(container) {{
                if (!container) return;
                const selected = container.querySelectorAll('input[type="checkbox"]:checked').length;
                const total = container.querySelectorAll('input[type="checkbox"]').length;
                container.querySelector('.fsw-selected-count').textContent = selected;
                container.querySelector('.fsw-total-count').textContent = total;
            }}

            document.addEventListener('DOMContentLoaded', function() {{
                document.querySelectorAll('.formula-selector-widget').forEach(container => {{
                    fswUpdateCounter(container);
                }});
            }});
        </script>
        '''

        return mark_safe(html)

    def value_from_datadict(self, data, files, name):
        values = data.getlist(name)
        return values

class WarehouseRelationAdminForm(forms.ModelForm):
    formula_ids = forms.MultipleChoiceField(
        required=False,
        widget=FormulaSelectorWidget(),
        label="فرمول‌های مجاز",
        help_text="فرمول‌هایی که در این رابطه نمایش داده می‌شوند را انتخاب کنید.",
        choices=[],
    )

    class Meta:
        model = WarehouseRelation
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            from SepidarApp.databaseConnector import db
            db.connect()
            all_formulas = get_all_formulas_from_sepidar()
            self.fields['formula_ids'].choices = [
                (str(f['id']), f"{f['code']} - {f['title']}")
                for f in all_formulas
            ]
            logger.warning(f"✅ {len(all_formulas)} formula choices loaded")
        except Exception as e:
            logger.error(f"❌ Error loading formula choices: {e}", exc_info=True)
            self.fields['formula_ids'].choices = []

        if self.instance and self.instance.pk:
            selected_ids = list(
                self.instance.formula_relations
                    .filter(is_deleted=False)
                    .values_list('formula_id', flat=True)
            )
            self.fields['formula_ids'].initial = [str(x) for x in selected_ids]

    def save(self, commit=True):
        logger.warning(f"🚀 form.save() called, commit={commit}")

        # pop کن
        selected_ids = self.cleaned_data.pop('formula_ids', [])
        logger.warning(f"📋 selected_ids popped: {selected_ids}")

        # ذخیره instance (جنگو خودش با commit=False می‌گیره)
        instance = super().save(commit=commit)
        logger.warning(f"✅ super().save() OK, pk={instance.pk}")

        # ✅ فرمول‌ها رو توی attribute ذخیره کن تا admin بعداً استفاده کنه
        instance._pending_formula_ids = selected_ids
        logger.warning(f"📦 _pending_formula_ids stored: {selected_ids}")

        # اگه commit=True، همین‌جا ذخیره کن
        if commit and instance.pk:
            self.save_formulas(instance, selected_ids)

        return instance

    @staticmethod
    def save_formulas(instance, selected_ids):
        """ذخیره فرمول‌های انتخاب‌شده"""
        logger.warning(f"🎯 save_formulas called for pk={instance.pk}")

        # نرمال‌سازی
        normalized_ids = []
        for x in selected_ids:
            try:
                normalized_ids.append(int(x))
            except (ValueError, TypeError):
                continue

        logger.warning(f"📋 normalized_ids: {normalized_ids}")

        try:
            all_formulas = {f['id']: f for f in get_all_formulas_from_sepidar()}
            logger.warning(f"📋 all_formulas count: {len(all_formulas)}")
        except Exception as e:
            logger.error(f"❌ Failed to fetch formulas: {e}", exc_info=True)
            return

        # حذف
        current_rfs = {rf.formula_id: rf for rf in instance.formula_relations.all()}
        logger.warning(f"📋 current_rfs: {list(current_rfs.keys())}")

        ids_to_remove = set(current_rfs.keys()) - set(normalized_ids)
        if ids_to_remove:
            deleted_count, _ = instance.formula_relations.filter(
                formula_id__in=ids_to_remove
            ).delete()
            logger.warning(f"🗑️ removed {deleted_count} items")

        # اضافه/بروزرسانی
        for fid in normalized_ids:
            if fid in all_formulas:
                f = all_formulas[fid]
                try:
                    obj, created = RelationFormula.objects.update_or_create(
                        relation=instance,
                        formula_id=fid,
                        defaults={
                            'formula_code': f['code'],
                            'formula_title': f['title'],
                            'formula_item_ref': f['item_ref'],
                            'formula_product_name': f['product_name'],
                            'is_deleted': False,
                            'deleted_at': None,
                        }
                    )
                    logger.warning(f"  {'✅ CREATED' if created else '🔄 UPDATED'} formula {fid}")
                except Exception as e:
                    logger.error(f"❌ Failed to save formula {fid}: {e}", exc_info=True)
            else:
                logger.warning(f"  ⚠️ formula {fid} not in all_formulas")

        logger.warning(f"✅ Final count: {instance.formula_relations.count()}")