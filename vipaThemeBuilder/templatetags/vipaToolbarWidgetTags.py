from django import template
from django.db.models import Q
from ..vipaThemeDataClass.buttonDataClass import IconBadgeButton, toolbarButton
from ..vipaThemeDataClass.actionsDataClass import *
from .vipaUtils import str2ction_if_need

register = template.Library()

@register.inclusion_tag('templates_tags/widgets/toolbar-button.html')
def toolbar_buttons( toolbar:toolbarButton ):
    defualt_toolbar = toolbarButton(
        title="عنوان",
        buttons=[
                IconBadgeButton("btn1", "دکمه ۱", action='POST:/btn_click', 
                                badge_color="#1FD85359",icon="""<i class="ki-duotone ki-abstract-26 fs-2x text-success">
                                                                            <span class="path1"></span>
                                                                            <span class="path2"></span>
                                                                        </i>"""),
            
                IconBadgeButton("btn2", "دکمه ۲", action='POST:/btn_click',
                                badge_color="#EFDA1E81",icon="""<i class="ki-duotone ki-pencil fs-2x text-warning">
                                                                            <span class="path1"></span>
                                                                            <span class="path2"></span>
                                                                        </i>"""),
            ]
    )
    
    
    if toolbar is None:
        toolbar = defualt_toolbar
    #----------------------------------------------------------------
    # click_action = str2ction_if_need(click_action)
    for btn in toolbar.buttons:
        btn.action = str2ction_if_need(btn.action)


        
    return {'buttons':toolbar.buttons,
            'toolbar': toolbar,
            }  