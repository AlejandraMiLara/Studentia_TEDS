from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UsuarioPersonalizado, Curso, Reporte, Actividad, Examen, Pregunta, Opcion
from django.forms import modelformset_factory, inlineformset_factory
from django.forms.models import inlineformset_factory


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
            'username': forms.TextInput(attrs={
                'readonly': 'readonly',
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'sobre_mi': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control'
            }),
            'rol': forms.Select(attrs={
                'class': 'form-control'
            }),

        }

        help_texts = {
            'username': '',
            'foto_perfil': '',
            'email': '',
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

    class Meta:
        fields = ['codigo_acceso']
        widgets = {
            'codigo_acceso': forms.TextInput(attrs={
                'class': 'form-control'
            })
        }


class ReportarForm(forms.ModelForm):
    class Meta:
        model = Reporte
        fields = ['motivo']
        widgets = {
            'motivo': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Describe el motivo del reporte',
                'rows': 4,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motivo'].required = False

    def clean_motivo(self):
        motivo = self.cleaned_data.get('motivo', '').strip()
        if not motivo:
            raise forms.ValidationError("Por favor, ingrese el motivo del reporte.")
        return motivo

   

class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = ['titulo', 'contenido', 'archivo', 'entregable', 'generado_por_ia', 'permite_entrega_tardia']

class ExamenForm(forms.ModelForm):
    class Meta:
        model = Examen
        fields = ['titulo', 'descripcion', 'fecha_inicio', 'fecha_fin', 'entregas_tardias']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.fecha_inicio:
                self.initial['fecha_inicio'] = self.instance.fecha_inicio.strftime('%Y-%m-%d')
            if self.instance.fecha_fin:
                self.initial['fecha_fin'] = self.instance.fecha_fin.strftime('%Y-%m-%d')

class PreguntaForm(forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = ['texto', 'tipo']
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
        }

OpcionFormSet = inlineformset_factory(
    Pregunta,
    Opcion,
    fields=['texto', 'es_correcta'],
    extra=2,
    can_delete=True
)

class OpcionForm(forms.ModelForm):
    class Meta:
        model = Opcion
        fields = ['texto', 'es_correcta']
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 2, 'cols': 30}),
        }

class VerdaderoFalsoForm(forms.Form):
    respuesta = forms.ChoiceField(
        choices=[('verdadero', 'Verdadero'), ('falso', 'Falso')],
        widget=forms.RadioSelect,
        label="Respuesta correcta"
    )
    