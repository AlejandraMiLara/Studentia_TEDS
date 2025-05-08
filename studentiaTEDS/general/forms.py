from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UsuarioPersonalizado, Curso, Reporte, Actividad

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'type': 'email', 'placeholder': 'Ingresa tu correo electrónico'})
    )

    class Meta:
        model = UsuarioPersonalizado
        fields = ('username', 'email', 'rol', 'sobre_mi', 'foto_perfil', 'password1', 'password2')

class EditarPerfilForm(forms.ModelForm):
    class Meta:
        model = UsuarioPersonalizado
        fields = ('username', 'email', 'rol', 'sobre_mi', 'foto_perfil')

        widgets = {
            'sobre_mi': forms.Textarea(attrs={'rows':4}),
        }

class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ['nombre_curso', 'descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }

class InscripcionCursoForm(forms.Form):
    codigo_acceso = forms.CharField(label="Código de Curso", max_length=10, required=True)

class ReportarForm(forms.ModelForm):
    class Meta:
        model = Reporte
        fields = ['motivo']        

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['titulo', 'contenido', 'archivo', 'entregable', 'generado_por_ia', 'permite_entrega_tardia']
