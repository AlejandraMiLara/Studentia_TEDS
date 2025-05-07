from django.urls import path, include
from django.contrib import admin
from general import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from general.views import CustomPasswordResetView, CustomPasswordResetConfirmView

urlpatterns = [
    #primer sprint
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),
    path('login/', views.iniciar_sesion, name="iniciar_sesion"),
    path('logout/', views.salir, name='salir'),
    path('signup/', views.registrar_usuario, name="registrar_usuario"),
    path('recovery/send/', auth_views.PasswordResetDoneView.as_view(template_name='recovery/password_reset_done.html'), name='password_reset_done'),
    path('recovery/completo/', auth_views.PasswordResetCompleteView.as_view(template_name='recovery/password_reset_complete.html'), name='password_reset_complete'),
    path('recovery/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('recovery/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    #segundo sprint
    path('profile/', views.ver_perfil, name='ver_perfil'),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)