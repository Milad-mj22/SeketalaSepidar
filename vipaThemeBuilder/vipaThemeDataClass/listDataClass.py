from dataclasses import dataclass

@dataclass
class listType1Item:
    title:str
    descriptione:str = ""
    tag:str = ""
    title_color:str = "#202020"
    descriptione_color:str = "#636363"
    badge_color:str = "#502090"
    title_font_weight:str= "bold"
    descriptione_font_weight:str= "normal"
    tag_font_weight:str= "bold"


