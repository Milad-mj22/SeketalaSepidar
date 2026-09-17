from django.urls import path, include
from . import views


app_name='sepidarApp'

urlpatterns = [
    # path('', views.dashboard_page, name='dashboard_page'),
    # path('', views.first_page,         name='sepidar_main_page'),
    
    path('', views.formula_list, name='formula_list'),
    path('formulas/', views.formula_list, name='formula_list'),
    path('formula/<int:formula_id>/', views.formula_detail, name='formula_detail'),
    path('api/formulas/<int:formula_id>/', views.api_formulas, name='api_formulas'),
    path('api/search-formulas/', views.search_formulas, name='search_formulas'),
    path('change_sl_acc_ref/', views.change_sl_acc_ref, name='change_sl_acc_ref'),


    path('auto_order/', views.auto_order, name='auto_order'),
    path('api/get_materials/', views.get_materials, name='get_materials'),
    path('api/submit-materials/', views.submit_materials, name='submit_materials'),
 
    path('api/submit-all-formula-values/', views.submit_all_formula_values, name='submit_all_formula_values'),
]


