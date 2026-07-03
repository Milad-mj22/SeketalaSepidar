# Create your views here.
from django.urls import path

from SekeSepidar import settings
from . import views


urlpatterns = [
    path('', views.about, name='about'),
]
