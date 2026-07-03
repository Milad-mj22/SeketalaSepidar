from django.urls import path, include
from . import views

app_name = 'SepidarApp'

urlpatterns = [
    # path('', views.dashboard_page, name='dashboard_page'),
    path('', views.first_page, name='sepidar_main_page'),
    
]

