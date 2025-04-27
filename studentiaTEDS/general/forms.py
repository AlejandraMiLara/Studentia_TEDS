from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UsuarioPersonalizado

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = UsuarioPersonalizado
        fields = ('username', 'email', 'rol', 'sobre_mi', 'foto_perfil', 'password1', 'password2')
