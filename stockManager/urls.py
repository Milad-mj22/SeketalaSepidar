

from django.urls import path, include
from django.conf.urls.static import static

from SekeSepidar import settings
from . import views

app_name = 'stockManager'

urlpatterns = [
    # path('', views.dashboard_page, name='dashboard_page'),
    path('', views.material_adjustment_page, name='main_page'),
    path('save-material-adjustments/', views.save_material_adjustments, name='material_adjustment_page'),
    path('items2buy/', views.low_stock_report_page, name='low_stock_report'), 
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



