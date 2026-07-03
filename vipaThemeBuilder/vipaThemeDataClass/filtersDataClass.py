from __future__ import annotations
from dataclasses import dataclass

@dataclass
class dropDownFilter:
    name:str
    label:str
    options:list[optionItem]
    descriptione:str = ""
    TYPE:str = 'dropdown' #don't change

@dataclass
class optionItem:
    name:str
    label:str

