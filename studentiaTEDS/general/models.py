from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class UsuarioPersonalizado(AbstractUser):
    ROLES = (
        ('Estudiante', 'Estudiante'),
        ('Profesor', 'Profesor')
    )
    rol = models.CharField(max_length=10, choices=ROLES, default='Estudiante')

    sobre_mi = models.TextField(max_length=2000, blank=True, null=True)

    foto_perfil = models.ImageField(upload_to='fotos_perfil/', blank=True, null=True)

    def __str__(self):
        return f"{self.username}({self.rol})"
