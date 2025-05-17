from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.db.models import Count

#primer sprint

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

#segundo sprint

class Curso(models.Model):
    id_profesor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nombre_curso = models.CharField(max_length=100)
    descripcion = models.TextField(max_length=500)
    codigo_acceso = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.nombre_curso

class ConfiguracionCurso(models.Model):
    ESTADOS = [
        (1, 'Activo'),
        (2, 'Borrador'),
        (3, 'Eliminado'),
    ]

    curso = models.OneToOneField(Curso, on_delete=models.CASCADE)
    estado = models.IntegerField(choices=ESTADOS, default=1)

    def __str__(self):
        return f"Configuración de {self.curso.nombre_curso}"

class AlumnoCurso(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    alumno = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.alumno.username} en {self.curso.nombre_curso}"
    
class Reporte(models.Model):
    reportante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reportes_realizados'
    )
    reportado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reportes_recibidos'
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, null=True, blank=True)
    motivo = models.TextField()
    contenido = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.reportante.username} reportó a {self.reportado.username}"
    
class Actividad(models.Model):
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='actividades_creadas'
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    archivo = models.FileField(upload_to='actividades/', null=True, blank=True)
    entregable = models.BooleanField(default=True)
    generado_por_ia = models.BooleanField(default=False)
    titulo = models.CharField(max_length=255)
    contenido = models.TextField()
    permite_entrega_tardia = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.titulo} - {self.curso.nombre_curso}"

class Envio(models.Model):
    alumno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='envios_realizados'
    )
    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='envios_recibidos'
    )
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    archivo = models.FileField(upload_to='envios/')
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.alumno.username} envió {self.actividad.titulo}"


#Tercer Sprint 

class Examen(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    entregas_tardias = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.titulo)
            slug = base_slug
            contador = 1
            while Examen.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{contador}"
                contador += 1
            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.titulo

class Pregunta(models.Model):
    TIPO_PREGUNTA_CHOICES = [
        ('abierta', 'Abierta'),
        ('opcion_multiple', 'Opción Múltiple'),
        ('verdadero_falso', 'Verdadero/Falso'),
    ]

    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)
    texto = models.CharField(max_length=255)
    tipo = models.CharField(max_length=20, choices=TIPO_PREGUNTA_CHOICES, default='abierta')

    def __str__(self):
        return self.texto

class Opcion(models.Model):
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    texto = models.CharField(max_length=255)
    es_correcta = models.BooleanField(default=False)

    def __str__(self):
        return self.texto
    
class Respuesta(models.Model):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE)
    estudiante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    respuesta_texto = models.TextField(blank=True, null=True)
    opcion_seleccionada = models.ForeignKey(Opcion, null=True, blank=True, on_delete=models.SET_NULL)
    puntaje = models.PositiveIntegerField(null=True, blank=True)
    comentario = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('examen', 'estudiante', 'pregunta')
        
        
