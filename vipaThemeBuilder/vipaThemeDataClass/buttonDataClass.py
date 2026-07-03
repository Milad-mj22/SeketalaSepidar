from dataclasses import dataclass
from .actionsDataClass import *

@dataclass
class IconBadgeButton:
    name:str
    label:str
    action:str|jsAction|urlAction|postAction = None
    text_color:str = "#202020"
    badge_color:str = "#1FD85359"
    bg_color:str= "transparent"
    font_weight:str = "bold"
    icon:str = """<i class="ki-duotone ki-abstract-26 fs-2x text-success"><span class="path1"></span><span class="path2"></span></i>"""
    padding:int=1
    label_pos:str = "bottom" #top left right
    icon_size:int = 40 #can be 20, 25, 35 and so on
    font_weight:str = "bold"


@dataclass
class toolbarButton:
    title:str
    buttons:list[IconBadgeButton]
    direction:str = 'v' # 'v' or 'h'
    padding:int = 5
    buttons_gap:int = 3
    bg_color:str = "#ffffff"






