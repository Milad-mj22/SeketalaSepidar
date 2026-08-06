import logging

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


# در templatetags/vipaUtilsTag.py
@register.filter
def exists_in_list(value, list_obj):
    """Check if value exists in list"""
    try:
        return str(value) in [str(item) for item in list_obj]
    except:
        return False

@register.filter
def get_quantity(list, key):
    """Get quantity from dictionary by key"""
    try:

        for dict in list:
            if dict['code'] ==key:
                value = dict.get('quantity', {})
                # print(f'code { dict['code']} , value : {value}')
                return value


        return 0

    except:
        return 0


logger = logging.getLogger(__name__)


@register.filter
def log_value(value):
    """Log value and return it"""
    logger.info(f'🔍 LOG VALUE: {value}')
    print(f'🔍 LOG VALUE: {value}')
    return value

@register.filter
def log_debug(value, label=''):
    """Log value with label and return it"""
    print(f'🔍 {label}: {value}')
    return value