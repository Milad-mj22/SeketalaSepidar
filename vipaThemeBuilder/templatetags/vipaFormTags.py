from django import template
from django.forms.widgets import CheckboxInput
from django.forms.fields import Field
register = template.Library()


@register.inclusion_tag('templates_tags/widgets/field_render.html')
def render_field(field:Field):
    return {
        'field': field,
        'label': field.label,
        'is_checkbox': field.widget_type== 'checkbox',
        'help_text': field.help_text,
        # 'tooltip_title': field.t,
    }


# @register.inclusion_tag('templates_tags/widgets/field_render.html')
# def render_field_by_info(field_info):
#     return {
#         'field': field_info,
#         'label': field_info.get('label', ''),
#         'help_text': field_info.get('help_text', ''),
#         'tooltip_title': field_info.get('title', ''),
#     }