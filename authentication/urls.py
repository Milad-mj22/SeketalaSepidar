from django.urls import path, include
from . import views

app_name = 'authentication'

urlpatterns = [
    # path('', views.dashboard_page, name='dashboard_page'),
    path('sign-in', views.login_page, name='sign-in'),
    path('sign-up', views.register_page, name='register_page'),
    path('sign-out', views.logout_user, name='logout_page'),
    path('register', views.register_api, name='register_page'),
    path('check-login', views.check_login, name='check_login'),
    path('profile-page', views.show_profile_page, name='show_profile_page'),
    path('forget-password', views.reset_password, name='reset_password'),
    
    
    path("admin/change-password/<int:pk>/", views.admin_change_password, name="admin_change_password"),
    path("admin/delete-user/<int:pk>/", views.delete_user, name="delete_user"),
    
]

