from django.urls import path, include
from django.contrib import admin
from general import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),
    path('login/', views.iniciar_sesion, name="iniciar_sesion"),
    path('logout/', views.salir, name='salir'),
]
