from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
import datetime
from django.contrib.auth import authenticate, login, logout, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import random
import string

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