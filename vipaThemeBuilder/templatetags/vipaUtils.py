from ..vipaThemeDataClass.actionsDataClass import *


def str2ction(text:str):
    if text is None:
        return None
    assert text.count(':') == 1, "wrong string format, ony one : should be exist"
    _type, value = text.split(':')
    if _type == 'JS':
        return jsAction(func_name=value)
    elif _type == 'URL':
        return urlAction(url=value)
    elif _type == 'POST':
        return postAction(url=value)
    else:
        raise "wrong type for string only JS: and URL: support"
    
def str2ction_if_need(inpt:str|jsAction|urlAction):
    if isinstance(inpt, str):
        return str2ction(inpt)
    else:
        return inpt
    

# myapp/templatetags/custom_filters.py
