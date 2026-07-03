from dataclasses import dataclass
from .filtersDataClass import dropDownFilter

@dataclass
class tabelItem:
    text:int|str
    symbol_img:str|None = None
    symbol_size:str="50px"
    color:str = "#202020"
    badge_color:str|None = None
    bg_color:str = "transparent"
    font_weight:str = "normal"

@dataclass
class tableheader:
    name:str
    label:str
    color:str = "#616161"
    # badge_color:str|None = None
    bg_color:str = "transparent"
    font_weight:str = "bold"

@dataclass
class tableDataClass:
    tabel_id:str
    headers:list[tableheader]
    datas:dict[str,list[tabelItem]]
    filters:list[dropDownFilter]|None = None
    selectable:bool = True
    per_page:int = 10
    bg_color:str="#ffffff"