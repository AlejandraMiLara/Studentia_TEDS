from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
import datetime
from django.contrib.auth import authenticate, login, logout, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import random
import string
from .forms import RegistroUsuarioForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView

#primer sprint

def inicio(request):
    return render(request, 'inicio.html')

def iniciar_sesion(request):
    msj = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('inicio')
        else:
            msj = "Correo o contraseña incorrectas. Intente de nuevo"
    return render(request, 'iniciar_sesion.html', {'msj':msj})

def salir(request):
    logout(request)
    return redirect('inicio')

def registrar_usuario(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()


            backend = get_backends()[0] 
            user.backend = f"{backend.__module__}.{backend.__class__.__name__}"

            login(request, user) 

            return redirect('inicio')
    else:
        form = RegistroUsuarioForm()

    return render(request, 'registrar_usuario.html', {'form': form})

class CustomPasswordResetView(PasswordResetView):
    template_name = 'recovery/password_reset.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_submitted'] = self.request.method == 'POST'
        return context

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'recovery/password_reset_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_submitted'] = self.request.method == 'POST'
        return context
    
#segundo sprint

@login_required
def ver_perfil(request):
    return render(request, 'perfil.html', {'usuario':request.user})