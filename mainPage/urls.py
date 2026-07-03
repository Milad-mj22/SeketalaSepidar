from django.urls import path, include
from . import views

app_name = 'mainPage'

urlpatterns = [
    # path('', views.dashboard_page, name='dashboard_page'),
    path('', views.main_page, name='main_page'),

    
    

]

