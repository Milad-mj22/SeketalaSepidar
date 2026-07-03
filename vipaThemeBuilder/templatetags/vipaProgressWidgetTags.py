from django import template
from django.db.models import Q

register = template.Library()

@register.inclusion_tag('templates_tags/widgets/circle-progress.html')
def circle_progress( percent:int, label:str, wgt_id:str ):
    
        
    return {'percent':percent,
            'label':label,
            'id':wgt_id,
            }  