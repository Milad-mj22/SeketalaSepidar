from django.urls import path, include
from . import views

app_name = 'licenseapp'

urlpatterns = [
    # path('', views.dashboard_page, name='dashboard_page'),
    path('activate/', views.activate_license, name='activate_license'),
    path("api/get-online-license/", views.get_online_license, name="get_online_license"),
    path("api/verify-license/", views.verify_license_api, name="verify_license_api"),


    
]

