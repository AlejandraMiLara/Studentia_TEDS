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
    path('profile/edit', views.editar_perfil, name='editar_perfil'),
    path('new/course', views.crear_curso, name='crear_curso'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path("course/join", views.inscribirse_curso, name="inscribirse_curso"),
    path("board/<str:codigo_acceso>", views.board, name="board"),
    path("board/<str:codigo_acceso>/leave", views.board_leave, name="board_leave"),
    path("board/<str:codigo_acceso>/delete", views.board_borrar, name="board_borrar"),
    path("board/<str:codigo_acceso>/update", views.board_actualizar, name="board_actualizar"),
    path("board/<str:codigo_acceso>/view/students", views.board_view_students, name="board_view_students"),
    path("board/<str:codigo_acceso>/remove/<int:id_alumno>", views.board_remove_student, name="board_remove_student"),
    path('profile/view/<int:id>', views.other_profile, name='other_profile'),
    path('report/student/<int:id>', views.report, name="report"),
    path('report/student/success', views.report_success, name="report_success"),
    path("board/<str:codigo_acceso>/add/content", views.board_add_content, name="board_add_content"),
    path("board/<str:codigo_acceso>/actividad/<int:id_actividad>/edit", views.content_edit, name="content_edit"),
    path("board/<str:codigo_acceso>/actividad/<int:id_actividad>/delete", views.content_delete, name="content_delete"),
    path('board/<str:codigo_acceso>/actividad/<int:id_actividad>/view', views.content_detail, name='content_detail'),


]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)