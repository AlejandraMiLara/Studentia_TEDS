from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UsuarioPersonalizado

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