from django import template
from ..vipaThemeDataClass.actionsDataClass import *
register = template.Library()

@register.filter
def has_active_sub(tree_page, active_page_name):
    return any(sub['name'] == active_page_name for sub in tree_page.get('subs', []))


@register.filter
def build_js_action(func_name:str):
    return jsAction(func_name)

@register.filter
def build_url_action(url:str):
    return urlAction(url)



import json


@register.filter
def to_json(value):
    """تبدیل شیء پایتون به JSON برای استفاده در JavaScript"""
    return json.dumps(value, default=str)