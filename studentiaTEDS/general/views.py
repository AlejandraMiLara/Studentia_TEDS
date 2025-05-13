from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
import datetime
from django.contrib.auth import authenticate, login, logout, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import random
import string
from .forms import RegistroUsuarioForm, EditarPerfilForm, CursoForm, InscripcionCursoForm, ReportarForm, ActividadForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from .models import Curso, AlumnoCurso, UsuarioPersonalizado, Actividad

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

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('ver_perfil')
    else:
        form = EditarPerfilForm(instance=request.user)

    return render(request, 'editar_perfil.html', {'form': form})

def generar_codigo():
    while True:
        codigo = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Curso.objects.filter(codigo_acceso=codigo).exists():
            return codigo

@login_required
def crear_curso(request):
    if request.user.rol != 'Profesor': 
        messages.error(request, "No tienes permiso para crear cursos.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = CursoForm(request.POST)
        if form.is_valid():
            curso = form.save(commit=False)
            curso.id_profesor = request.user 
            curso.codigo_acceso = generar_codigo()
            curso.save()
            return redirect('dashboard')

    else:
        form = CursoForm()

    return render(request, 'crear_curso.html', {'form': form})

@login_required
def dashboard(request):
    usuario = request.user
    es_profesor = usuario.rol == "Profesor"
    if es_profesor:
        cursos_creados = Curso.objects.filter(id_profesor=usuario) 
    else:
        cursos_creados = None

    cursos_inscritos = AlumnoCurso.objects.filter(alumno=usuario) 

    return render(request, "dashboard.html", {
        "es_profesor": es_profesor,
        "cursos_creados": cursos_creados,
        "cursos_inscritos": cursos_inscritos
    })

@login_required
def board(request, codigo_acceso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividades = Actividad.objects.filter(curso=curso).order_by('-fecha')

    return render(request, 'board.html',{
        'curso':curso,
        'actividades': actividades
    })

def board_leave(request, codigo_acceso):
    usuario = request.user
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    inscripcion = get_object_or_404(AlumnoCurso, alumno=usuario, curso=curso)

    if request.method == "POST":
        inscripcion.delete()
        return redirect('dashboard')
    
    return render(request, 'board_leave.html', {
        "curso":curso
    })

@login_required
def board_borrar(request, codigo_acceso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    if request.method == "POST":
        curso.delete()
        return redirect('dashboard')
    return render(request, 'board_borrar.html', {'curso':curso})

@login_required
def board_actualizar(request, codigo_acceso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    if request.method == "POST":
        form = CursoForm(request.POST, instance=curso)

        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = CursoForm(instance=curso)
    
    return render(request, 'board_actualizar.html', {
        'form':form, 'curso':curso
    })

@login_required
def inscribirse_curso(request):
    if request.method == "POST":
        form = InscripcionCursoForm(request.POST)
        if form.is_valid():
            codigo_acceso = form.cleaned_data["codigo_acceso"]

            # Buscar el curso por su código de acceso
            curso = Curso.objects.filter(codigo_acceso=codigo_acceso).first()

            # Validar que el curso existe
            if not curso:
                messages.error(request, "El curso no existe.")
                return redirect("inscribirse_curso")

            # Validar que el profesor no intente inscribirse en su propio curso
            if curso.id_profesor == request.user:
                messages.error(request, "No puedes inscribirte en tu propio curso.")
                return redirect("inscribirse_curso")

            # Verificar si el usuario ya está inscrito en el curso
            if AlumnoCurso.objects.filter(curso=curso, alumno=request.user).exists():
                # Si ya está inscrito, mostrar el mensaje de error
                messages.error(request, "Ya estás inscrito en este curso.")
                return redirect("inscribirse_curso")  # Redirigir para que el mensaje se vea

            # Si no está inscrito, registrar la inscripción
            AlumnoCurso.objects.create(curso=curso, alumno=request.user)
            messages.success(request, f"Te has inscrito en {curso.nombre_curso} correctamente.")

            # Redirigir al dashboard
            return redirect("dashboard")

    else:
        form = InscripcionCursoForm()

    return render(request, "inscribirse_curso.html", {"form": form})

@login_required
def board_view_students(request, codigo_acceso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    alumnos_inscritos = AlumnoCurso.objects.filter(curso=curso).select_related('alumno')

    return render(request, 'board_view_students.html', {
        'curso':curso,
        'alumnos_inscritos':alumnos_inscritos
    })

@login_required
def board_remove_student(request, codigo_acceso, id_alumno):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    if request.user != curso.id_profesor:
        return redirect('dashboard')

    if request.method == "POST":
        AlumnoCurso.objects.filter(curso=curso, alumno_id=id_alumno).delete()

    return redirect('board_view_students', codigo_acceso=codigo_acceso)

from django.http import HttpResponseForbidden
from django.db.models import Q

@login_required
def other_profile(request, id):
    usuario = request.user
    alumno = get_object_or_404(UsuarioPersonalizado, id=id)

    if usuario.id == alumno.id:
        return redirect('ver_perfil')

    # Verificar relación académica:
    # Caso 1: Ambos son alumnos del mismo curso
    cursos_comunes = AlumnoCurso.objects.filter(
        curso__in=AlumnoCurso.objects.filter(alumno=usuario).values('curso'),
        alumno=alumno
    ).exists()

    # Caso 2: Usuario logueado es profesor de un curso donde el otro es alumno
    como_profesor = Curso.objects.filter(
        id_profesor=usuario,
        alumnocurso__alumno=alumno
    ).exists()

    # Caso 3: Usuario logueado es alumno en curso impartido por el otro (profesor)
    como_estudiante = Curso.objects.filter(
        id_profesor=alumno,
        alumnocurso__alumno=usuario
    ).exists()

    if not (cursos_comunes or como_profesor or como_estudiante):
        return render(request, '403.html', status=403)

    return render(request, 'other_profile.html', {'alumno': alumno})


@login_required
def report(request, id):
    usuario = request.user
    alumno = get_object_or_404(UsuarioPersonalizado, id=id)

    if request.method == "POST":
        form = ReportarForm(request.POST)

        if form.is_valid():
            reporte = form.save(commit=False)
            reporte.reportante = usuario
            reporte.reportado = alumno
            reporte.save()
            return redirect('report_success')
    else:
        form = ReportarForm()

    return render(request, 'report.html', {
        'form': form,
        'reportado': alumno,
        'reportante': usuario
    })


@login_required
def report_success(request):
    msj = "El reporte ha sido enviado. Nos pondremos en contacto contigo pronto"
    return render(request, 'report_success.html', {'msj':msj})

@login_required
def board_add_content(request, codigo_acceso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    if request.user != curso.id_profesor:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ActividadForm(request.POST, request.FILES)
        if form.is_valid():
            actividad = form.save(commit=False)
            actividad.curso = curso
            actividad.docente = request.user
            actividad.save()
            return redirect('board', codigo_acceso=curso.codigo_acceso)
    else:
        form = ActividadForm()

    return render(request, 'board_add_content.html', {
        'curso': curso,
        'form': form
    })


@login_required
def content_edit(request, codigo_acceso, id_actividad):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso)

    if request.user != curso.id_profesor:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ActividadForm(request.POST, request.FILES, instance=actividad)
        if form.is_valid():
            form.save()
            return redirect('board', codigo_acceso=codigo_acceso)
    else:
        form = ActividadForm(instance=actividad)

    return render(request, 'board_edit_content.html', {
        'curso': curso,
        'form': form
    })


@login_required
def content_delete(request, codigo_acceso, id_actividad):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso)

    if request.user != curso.id_profesor:
        return redirect('dashboard')

    if request.method == 'POST':
        actividad.delete()
        return redirect('board', codigo_acceso=codigo_acceso)

    return render(request, 'board_delete_content.html', {
        'curso': curso,
        'actividad': actividad
    })

@login_required
def content_detail(request, codigo_acceso, id_actividad):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso)

    return render(request, 'board_content_detail.html', {
        'curso': curso,
        'actividad': actividad,
    })
