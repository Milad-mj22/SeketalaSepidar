from django import template
from django.db.models import Q
from ..vipaThemeDataClass.listDataClass import listType1Item
register = template.Library()

@register.inclusion_tag('templates_tags/widgets/list_type1.html')
def list_type1(title, data=None, selectable=True):
    defualt_data = [
        listType1Item("کلاس عیب", "این کلاس نوع اول است", "قدیمی", badge_color="#502090"), 
        listType1Item("شکستگی عیب", "این کلاس نوع خرابی است", "جدید", badge_color="#BB2A6B"), 
    ]

    if data is None:
        data = defualt_data
        
    return {'title':title,
            'selectable':selectable,
            'items': data
            }  

