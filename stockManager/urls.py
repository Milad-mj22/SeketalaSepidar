

from django.urls import path, include
from django.conf.urls.static import static

from SekeSepidar import settings
from . import views

app_name = 'stockManager'

urlpatterns = [
    # path('', views.dashboard_page, name='dashboard_page'),
    path('', views.material_adjustment_page, name='main_page'),
    path('save-material-adjustments/', views.save_material_adjustments, name='material_adjustment_page'),
    path('home/',include('mainPage.urls')),
    path('authentication/', include('authentication.urls', namespace='authentication')),
    path('about/',include('aboutapp.urls')),
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



