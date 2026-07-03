# Create your views here.
from django.urls import path

from SekeSepidar import settings
from . import views

app_name = 'aboutapp'

urlpatterns = [
    path('about', views.about_page, name='about_page'),
]