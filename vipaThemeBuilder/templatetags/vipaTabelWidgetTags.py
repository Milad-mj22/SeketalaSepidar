from django import template
from django.db.models import Q
from ..vipaThemeDataClass.tablesDataClass import tabelItem, tableheader, tableDataClass
from ..vipaThemeDataClass.filtersDataClass import optionItem, dropDownFilter
from ..vipaThemeDataClass.actionsDataClass import *
from .vipaUtils import str2ction_if_need
register = template.Library()
from typing import TypedDict, Literal, List, Optional

# تعریف ساختار هر آیتم در لیست
class ActionItem(TypedDict):
    name: str
    type: Literal['url', 'js', 'str']  # این فیلد فقط می‌تواند یکی از این سه مقدار باشد
    value: str  # مقدار اصلی (URL، کد JS یا متن)


@register.inclusion_tag('templates_tags/widgets/pro_table.html')
def pro_tabel(table_data:tableDataClass|None,
              item_edit_action:urlAction|jsAction|str, 
              item_delete_action:urlAction|jsAction|str, 
              add_item_action:urlAction|jsAction|str, 
              filters_action:urlAction|jsAction|str, 
              search_action:urlAction|jsAction|str = None,
              filters:list=None,
              other_actions:Optional[List[ActionItem]] = None,
              datasets : list = None
              ):
    
    defualt_table_data = tableDataClass(
        tabel_id="vipa_table",
        headers=[
                tableheader("name", "نام"),
                tableheader("age", "سن"),
                tableheader("role", "نقش"),
            ],
        datas={
                "id": [1, 2], 
                "name":[tabelItem("علی", font_weight="bold"), tabelItem("رضا", font_weight="bold")], 
                "age": [tabelItem(25), tabelItem(30)],
                "role": [tabelItem("ادمین", badge_color="#a0d69e",), tabelItem("کاربر", badge_color="#21cfcf")]
            },
        filters=[ dropDownFilter('role', 'نقش', options=[optionItem('admin','ادمین'), optionItem('user', 'کاربر')])
                 ]
        )

    if table_data is None:
        table_data = defualt_table_data
    #-----------------------------------------------------------------------
    assert "id" in table_data.datas, "defualt_datas should have an extra column named 'id'"

    item_edit_action = str2ction_if_need(item_edit_action)
    item_delete_action = str2ction_if_need(item_delete_action)
    filters_action = str2ction_if_need(filters_action)
    add_item_action = str2ction_if_need(add_item_action)
    search_action = str2ction_if_need(search_action)




    count = len(table_data.datas[table_data.headers[0].name])
    data_for_table = []
    for i in range(count):
        row = {
            "id":table_data.datas['id'][i],
            "data":[],
        }
        for col in table_data.headers:
            row["data"].append( table_data.datas[col.name][i]
                               )
        data_for_table.append(row)



    return {'datas':data_for_table,
            'table_data':table_data,
            'item_delete_action':item_delete_action,
            'item_edit_action':item_edit_action,
            'other_actions':other_actions,
            'filters_action':filters_action,
            'add_item_action':add_item_action,
            'search_action':search_action,
            'datasets':datasets
            }  





# @register.inclusion_tag('templates_tags/widgets/pro_table.html')
# def pro_tabel2(columns:list[tableheader], 
#               datas:dict[str,list[tabelItem]], 
#               item_edit_action:urlAction|jsAction|str, 
#               item_delete_action:urlAction|jsAction|str, 
#               filters_submit_url:str, add_item_url:str, filters:list=None, selectable=True, tabel_id="vipa_table", per_page=10):
    
#     item_edit_action = str2ction_if_need(item_edit_action)

#     defualt_columns = [
#         tableheader("name", "نام"),
#         tableheader("age", "سن"),
#         tableheader("role", "نقش"),
#     ]

#     defualt_datas = {
#         "id": [1, 2], 
#         "name":[tabelItem("علی", font_weight="bold"), tabelItem("رضا", font_weight="bold")], 
#         "age": [tabelItem(25), tabelItem(30)],
#         "role": [tabelItem("ادمین", badge_color="#a0d69e",), tabelItem("کاربر", badge_color="#21cfcf")]
#     }

#     defualt_filters = [
#         dropDownFilter('role', 'نقش', options=[optionItem('admin','ادمین'), optionItem('user', 'کاربر')])
#     ]

#     if columns is None:
#         columns = defualt_columns
#     if datas is None:
#         datas = defualt_datas
#     if filters is None:
#         filters = defualt_filters
#     #-----------------------------------------------------------------------
#     assert "id" in defualt_datas, "defualt_datas should have an extra column named 'id'"

#     count = len(datas[columns[0].name])
#     data_for_table = []
#     for i in range(count):
#         row = {
#             "id":datas['id'][i],
#             "data":[],
#         }
#         for col in columns:
#             row["data"].append( datas[col.name][i]
#                                )
#         data_for_table.append(row)



#     return {'datas':data_for_table,
#             'columns':columns,
#             'item_delete_action':item_delete_action,
#             'item_edit_action':item_edit_action,
#             'filters_submit_url':filters_submit_url,
#             'add_item_url':add_item_url,
#             'filters':filters,
#             'selectable':selectable,
#             'tabel_id':tabel_id,
#             'per_page':per_page
#             }  