from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioPersonalizado, Curso, ConfiguracionCurso, Reporte, Envio

# Register your models here.

class UsuarioPersonalizadoAdmin(UserAdmin):
    model = UsuarioPersonalizado
    list_display = ['username', 'email', 'rol', 'is_active']

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('rol', 'sobre_mi', 'foto_perfil')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('rol', 'sobre_mi', 'foto_perfil')}),
    )

admin.site.register(UsuarioPersonalizado, UsuarioPersonalizadoAdmin)

class CursoAdmin(admin.ModelAdmin):
    list_display = ('nombre_curso', 'id_profesor', 'codigo_acceso', 'descripcion')
    search_fields = ('nombre_curso', 'id_profesor__username', 'codigo_acceso')

class ConfiguracionCursoAdmin(admin.ModelAdmin):
    list_display = ('curso', 'estado')
    search_fields = ('curso__nombre_curso',)

class AlumnoCursoAdmin(admin.ModelAdmin):
    list_display = ('curso', 'alumno')
    search_fields = ('curso__nombre_curso', 'alumno__username')

admin.site.register(Curso, CursoAdmin)
admin.site.register(ConfiguracionCurso, ConfiguracionCursoAdmin)

class ReporteAdmin(admin.ModelAdmin):
    list_display = ('reportante', 'reportado', 'curso', 'motivo')
    search_fields = ('reportante__username', 'reportado__username', 'curso__nombre_curso')

admin.site.register(Reporte, ReporteAdmin)

@admin.register(Envio)
class EnvioAdmin(admin.ModelAdmin):
    list_display = ('id', 'alumno', 'docente', 'curso', 'actividad', 'fecha', 'calificacion')
    list_filter = ('curso', 'actividad', 'docente', 'fecha')
    search_fields = ('alumno__username', 'docente__username', 'curso__nombre_curso', 'actividad__titulo')
    list_editable = ('calificacion',)
    readonly_fields = ('fecha',)
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)

    # Para mostrar correctamente el nombre del curso y actividad en el admin
    def curso_nombre(self, obj):
        return obj.curso.nombre_curso
    curso_nombre.short_description = 'Curso'

    def actividad_titulo(self, obj):
        return obj.actividad.titulo
    actividad_titulo.short_description = 'Actividad'
