from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
import datetime 
from django.contrib.auth import authenticate, login, logout, get_backends, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import random
import string
from .forms import RegistroUsuarioForm, EditarPerfilForm, CursoForm, InscripcionCursoForm, ReportarForm, ActividadForm, ExamenForm, PreguntaForm, OpcionForm, VerdaderoFalsoForm, EnvioForm, CalificacionForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from .models import Curso, AlumnoCurso, UsuarioPersonalizado, Actividad, Examen, Pregunta, Opcion, Respuesta, Intento, Envio
from django import forms
from django.forms import modelformset_factory, inlineformset_factory
from django.utils import timezone
from datetime import date
from django.contrib.auth.models import User
from django.db.models import Sum
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.exceptions import PermissionDenied
from .decorators import verificar_acceso_curso

from django.conf import settings
import openai
from openai import OpenAI
from django.views.decorators.csrf import csrf_exempt


client = OpenAI(api_key=settings.OPENAI_API_KEY)


User = get_user_model()

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
@verificar_acceso_curso
@login_required
def board(request, codigo_acceso, curso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividades = Actividad.objects.filter(curso=curso).order_by('-fecha')
    examenes = Examen.objects.filter(curso=curso).order_by('-fecha_inicio')
    hoy = date.today()
    return render(request, 'board.html',{
        'curso':curso,
        'actividades': actividades,
        'examenes': examenes,
        'hoy': hoy
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

    envio = Envio.objects.filter(alumno=request.user, actividad=actividad).first()
    ya_enviado = envio is not None
    calificacion = envio.calificacion if envio else None

    return render(request, 'board_content_detail.html', {
        'curso': curso,
        'actividad': actividad,
        'ya_enviado': ya_enviado,
        'calificacion': calificacion,
        'now': timezone.now(),
    })
    
    
    
    
    
    
    #Tercer Sprint
@login_required
def crear_examen(request, codigo_acceso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    if request.user != curso.id_profesor:
        return redirect('board', codigo_acceso=curso.codigo_acceso)

    if request.method == 'POST':
        form = ExamenForm(request.POST)
        if form.is_valid():
            examen = form.save(commit=False)
            examen.curso = curso
            examen.creado_por = request.user
            examen.save()
            messages.success(request, "Examen creado exitosamente")
            return redirect('listar_preguntas', slug=examen.slug)
        else:
            messages.error(request, "Error al crear el examen, intenta de nuevo")
    else:
        form = ExamenForm()

    return render(request, 'crear_examen.html', {'form': form, 'curso': curso})

@login_required
def agregar_pregunta(request, slug):
    
    examen = get_object_or_404(Examen, slug=slug)

    # Validar que solo el creador del examen pueda agregar preguntas
    if request.user != examen.creado_por:
        return redirect('board', codigo_acceso=examen.curso.codigo_acceso)

    # Formset para opciones de opción múltiple
    OpcionFormSet = modelformset_factory(
        Opcion,
        form=OpcionForm,
        extra=3,
        min_num=2,
        validate_min=True,
        max_num=5,
        validate_max=True,
        can_delete=True
    )

    vf_form = VerdaderoFalsoForm()
    formset = OpcionFormSet(queryset=Opcion.objects.none())  # Inicial vacío para GET

    if request.method == 'POST':
        pregunta_form = PreguntaForm(request.POST)
        tipo = request.POST.get('tipo')

        if not tipo:
            messages.error(request, "Debes seleccionar un tipo de pregunta.")
            return render(request, 'agregar_pregunta.html', {
                'pregunta_form': pregunta_form,
                'formset': formset,
                'vf_form': vf_form,
                'examen': examen,
            })

        if tipo == 'opcion_multiple':
            formset = OpcionFormSet(request.POST, queryset=Opcion.objects.none())

            if pregunta_form.is_valid() and formset.is_valid():
                pregunta = pregunta_form.save(commit=False)
                pregunta.examen = examen
                pregunta.tipo = tipo
                pregunta.save()

                opciones_correctas = 0
                opciones_guardadas = 0

                for opcion_form in formset:
                    if opcion_form.cleaned_data.get('DELETE'):
                        continue
                    
                    texto = opcion_form.cleaned_data.get('texto')
                    if not texto:
                        continue

                    opcion = opcion_form.save(commit=False)
                    opcion.pregunta = pregunta
                    opcion.save()
                    opciones_guardadas += 1

                    if opcion.es_correcta:
                        opciones_correctas += 1

                # Validaciones específicas para opción múltiple
                if opciones_guardadas < 2:
                    messages.error(request, "Debes ingresar al menos 2 opciones.")
                   # pregunta.delete()
                   # return redirect('agregar_pregunta', slug=examen.slug)
                elif opciones_correctas == 0:
                    messages.error(request, "Debes marcar al menos una opción como correcta.")
                    pregunta.delete()
                   # return redirect('agregar_pregunta', slug=examen.slug)
                else:
                    messages.success(request, "Pregunta de opción múltiple agregada correctamente.")
                    return redirect('listar_preguntas', slug=examen.slug)

        elif tipo == 'verdadero_falso':
            vf_form = VerdaderoFalsoForm(request.POST)

            if pregunta_form.is_valid() and vf_form.is_valid():
                pregunta = pregunta_form.save(commit=False)
                pregunta.examen = examen
                pregunta.tipo = tipo
                pregunta.save()

                respuesta = vf_form.cleaned_data['respuesta']
                Opcion.objects.create(
                    pregunta=pregunta,
                    texto='Verdadero',
                    es_correcta=(respuesta == 'verdadero')
                )
                Opcion.objects.create(
                    pregunta=pregunta,
                    texto='Falso',
                    es_correcta=(respuesta == 'falso')
                )

                messages.success(request, "Pregunta de Verdadero/Falso agregada correctamente.")
                return redirect('listar_preguntas', slug=examen.slug)
            else:
                error_message = "Error en el formulario: "
                if not pregunta_form.is_valid():
                    error_message += f"Pregunta - {pregunta_form.errors} "
                if not vf_form.is_valid():
                    error_message += f"VF - {vf_form.errors}"
                messages.error(request, error_message.strip())

        elif tipo == 'abierta':
            if pregunta_form.is_valid():
                pregunta = pregunta_form.save(commit=False)
                pregunta.examen = examen
                pregunta.tipo = tipo
                pregunta.save()
                messages.success(request, "Pregunta abierta agregada correctamente.")
                return redirect('listar_preguntas', slug=examen.slug)
            else:
                messages.error(request, f"Error en el formulario de pregunta abierta: {pregunta_form.errors}")

        else:
            messages.error(request, f"Tipo de pregunta inválido: {tipo}")

    else:
        pregunta_form = PreguntaForm()

    return render(request, 'agregar_pregunta.html', {
        'pregunta_form': pregunta_form,
        'formset': formset,
        'vf_form': vf_form,
        'examen': examen,
    })

@login_required
def listar_preguntas(request, slug):
    examen = get_object_or_404(Examen, slug=slug)

    if request.user != examen.creado_por:
        return redirect('board', codigo_acceso=examen.curso.codigo_acceso)

    preguntas = Pregunta.objects.filter(examen=examen)
    return render(request, 'listar_preguntas.html', {'examen': examen, 'preguntas': preguntas})

@login_required
def editar_pregunta(request, slug, pk):
    
    examen = get_object_or_404(Examen, slug=slug)
    pregunta = get_object_or_404(Pregunta, id=pk, examen=examen)

    if request.user != examen.creado_por:
        return redirect('board', codigo_acceso=examen.curso.codigo_acceso)

    tipo = pregunta.tipo
    vf_form = VerdaderoFalsoForm()
    formset = None

    # Obtener opciones actuales y calcular cuántos formularios vacíos se requieren
    opciones_existentes = Opcion.objects.filter(pregunta=pregunta)
    extra = max(0, 5 - opciones_existentes.count())

    OpcionFormSet = modelformset_factory(
        Opcion,
        form=OpcionForm,
        extra=extra,
        min_num=2,
        validate_min=True,
        max_num=5,
        validate_max=True,
        can_delete=True
    )

    if request.method == 'POST':
        pregunta_form = PreguntaForm(request.POST, instance=pregunta)
        pregunta_form.data = pregunta_form.data.copy()
        pregunta_form.data['tipo'] = pregunta.tipo
        
        pregunta_form.fields['tipo'].disabled = True

        if tipo == 'opcion_multiple':
            formset = OpcionFormSet(request.POST, queryset=opciones_existentes)

            if pregunta_form.is_valid() and formset.is_valid():
                pregunta = pregunta_form.save()

                opciones_correctas = 0
                opciones_guardadas = 0

                for opcion_form in formset:
                    if opcion_form.cleaned_data.get('DELETE'):
                        if opcion_form.instance.pk:
                            opcion_form.instance.delete()
                        continue

                    texto = opcion_form.cleaned_data.get('texto')
                    if not texto:
                        continue

                    opcion = opcion_form.save(commit=False)
                    opcion.pregunta = pregunta
                    opcion.save()
                    opciones_guardadas += 1

                    if opcion.es_correcta:
                        opciones_correctas += 1

                if opciones_guardadas < 2:
                    messages.error(request, "Debes mantener al menos 2 opciones.")
                elif opciones_correctas == 0:
                    messages.error(request, "Debe haber al menos una opción correcta.")
                    #pregunta.delete()
                else:
                    messages.success(request, "Pregunta de opción múltiple actualizada correctamente.")
                    return redirect('listar_preguntas', slug=slug)

        elif tipo == 'verdadero_falso':
            vf_form = VerdaderoFalsoForm(request.POST)

            if pregunta_form.is_valid() and vf_form.is_valid():
                pregunta = pregunta_form.save()
                respuesta = vf_form.cleaned_data['respuesta']

                opciones = Opcion.objects.filter(pregunta=pregunta)
                for opcion in opciones:
                    if opcion.texto.lower() == 'verdadero':
                        opcion.es_correcta = (respuesta == 'verdadero')
                    elif opcion.texto.lower() == 'falso':
                        opcion.es_correcta = (respuesta == 'falso')
                    opcion.save()

                messages.success(request, "Pregunta de Verdadero/Falso actualizada correctamente.")
                return redirect('listar_preguntas', slug=slug)

        elif tipo == 'abierta':
            if pregunta_form.is_valid():
                pregunta_form.save()
                messages.success(request, "Pregunta abierta actualizada correctamente.")
                return redirect('listar_preguntas', slug=slug)
            else:
                messages.error(request, f"Error en el formulario: {pregunta_form.errors}")

    else:
        pregunta_form = PreguntaForm(instance=pregunta)
        
        pregunta_form.fields['tipo'].disabled = True

        if tipo == 'opcion_multiple':
            formset = OpcionFormSet(queryset=opciones_existentes)

        elif tipo == 'verdadero_falso':
            opciones = Opcion.objects.filter(pregunta=pregunta)
            respuesta = 'verdadero' if opciones.filter(texto__iexact='verdadero', es_correcta=True).exists() else 'falso'
            vf_form = VerdaderoFalsoForm(initial={'respuesta': respuesta})

    return render(request, 'editar_pregunta.html', {
        'pregunta_form': pregunta_form,
        'formset': formset,
        'vf_form': vf_form,
        'examen': examen,
        'modo_edicion': True,
        'pregunta': pregunta,
    })

@login_required
def eliminar_pregunta(request, slug, pk):
    examen = get_object_or_404(Examen, slug=slug)
    pregunta = get_object_or_404(Pregunta, id=pk, examen=examen)

    if request.user != examen.creado_por:
        return redirect('board', codigo_acceso=examen.curso.codigo_acceso)

    if request.method == 'POST':
        pregunta.delete()
        messages.success(request, "Pregunta eliminada correctamente.")
        return redirect('listar_preguntas', slug=slug)

    return render(request, 'eliminar_pregunta.html', {'pregunta': pregunta, 'examen': examen})

@login_required
def ver_examen(request, slug):
    examen = get_object_or_404(Examen, slug=slug)
    es_docente = request.user == examen.creado_por
    ahora = timezone.now().date()

    disponible = examen.fecha_inicio <= ahora and (not examen.fecha_fin or examen.fecha_fin >= ahora)

    estado = "cerrado"
    if disponible:
        ya_respondido = Respuesta.objects.filter(examen=examen, estudiante=request.user).exists()
        estado = "respondido" if ya_respondido else "disponible"

    preguntas = Pregunta.objects.filter(examen=examen).prefetch_related('opcion_set') if es_docente else None

    return render(request, 'ver_examen.html', {
        'examen': examen,
        'es_docente': es_docente,
        'disponible': disponible,
        'estado': estado,
        'preguntas': preguntas,
    })

@login_required
def iniciar_examen(request, slug):
    examen = get_object_or_404(Examen, slug=slug)
    estudiante = request.user
    ahora = timezone.now().date()
    curso = examen.curso

    # Verificación de acceso
    if estudiante != examen.creado_por and not AlumnoCurso.objects.filter(curso=curso, alumno=estudiante).exists():
        raise PermissionDenied("No tienes permiso para presentar este examen.")

    if examen.fecha_inicio > ahora or (examen.fecha_fin and examen.fecha_fin < ahora):
        messages.error(request, "Este examen no está disponible en este momento.")
        return redirect('ver_examen', slug=examen.slug)

    if estudiante == examen.creado_por:
        messages.info(request, "Eres el creador del examen, no puedes presentarlo.")
        return redirect('ver_examen', slug=examen.slug)

    # ✅ Verificar si ya ha completado el examen
    if Respuesta.objects.filter(examen=examen, estudiante=estudiante).exists():
        messages.warning(request, "Ya respondiste este examen.")
        return redirect('ver_examen', slug=examen.slug)

    # ✅ Registrar intento si no existe
    intento, creado = Intento.objects.get_or_create(
        examen=examen,
        estudiante=estudiante,
        completado=False
    )

    if request.method == 'POST':
        for key, value in request.POST.items():
            if key.startswith('pregunta_'):
                pregunta_id = key.split('_')[1]
                try:
                    pregunta = Pregunta.objects.get(id=pregunta_id, examen=examen)

                    if pregunta.tipo == "abierta":
                        Respuesta.objects.create(
                            examen=examen,
                            estudiante=estudiante,
                            pregunta=pregunta,
                            respuesta_texto=value
                        )
                    else:
                        opcion = Opcion.objects.get(id=value, pregunta=pregunta)
                        Respuesta.objects.create(
                            examen=examen,
                            estudiante=estudiante,
                            pregunta=pregunta,
                            opcion_seleccionada=opcion
                        )
                except (Pregunta.DoesNotExist, Opcion.DoesNotExist):
                    continue

        # ✅ Marcar intento como completado
        intento.completado = True
        intento.save()

        messages.success(request, "Respuestas enviadas correctamente.")
        return redirect('ver_examen', slug=examen.slug)

    preguntas = Pregunta.objects.filter(examen=examen).prefetch_related('opcion_set')
    return render(request, 'iniciar_examen.html', {
        'examen': examen,
        'preguntas': preguntas,
    })

    
@login_required
def editar_examen(request, slug):
    
    examen = get_object_or_404(Examen, slug=slug)

    # Solo el profesor que creó el examen puede editarlo
    if request.user != examen.creado_por:
        messages.error(request, "No tienes permiso para editar este examen.")
        return redirect('ver_examen', slug=slug)

    if request.method == 'POST':
        form = ExamenForm(request.POST, instance=examen)
        if form.is_valid():
            examen_actualizado = form.save(commit=False)
            # Validar que el título no esté vacío (ya lo hace form.is_valid())
            if examen_actualizado.titulo.strip() == '':
                messages.error(request, "Por favor, ingrese un título.")
            # Validar que haya al menos una pregunta
            elif examen.pregunta_set.count() == 0:
                messages.error(request, "Debe haber al menos una pregunta.")
            else:
                examen_actualizado.save()
                messages.success(request, "Examen actualizado con éxito.")
                return redirect('ver_examen', slug=examen.slug)
        else:
            messages.error(request, "Error al actualizar el examen, intenta de nuevo.")
    else:
        form = ExamenForm(instance=examen)

    return render(request, 'editar_examen.html', {
        'form': form,
        'examen': examen,
    })

@login_required
def eliminar_examen(request, slug):
    examen = get_object_or_404(Examen, slug=slug)

    if request.user != examen.creado_por:
        raise PermissionDenied("No tienes permiso para eliminar este examen.")

    intentos_activos = Intento.objects.filter(examen=examen, completado=False)

    if intentos_activos.exists():
        # Si hay intentos activos, no lo eliminamos y mostramos los usuarios en la plantilla
        return render(request, 'eliminar_examen.html', {
            'examen': examen,
            'intentos_activos': intentos_activos
        })

    if request.method == 'POST':
        examen.delete()
        
        return redirect('board', codigo_acceso=examen.curso.codigo_acceso)



    return render(request, 'eliminar_examen.html', {
        'examen': examen,
        'intentos_activos': []
    })
    
@verificar_acceso_curso
@login_required
def examenes_por_calificar(request, codigo_acceso, curso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    if request.user != curso.id_profesor:
        return redirect('board', codigo_acceso=codigo_acceso)

    examenes = Examen.objects.filter(curso=curso)
    examenes_con_respuestas = []

    for examen in examenes:
        estudiantes_con_respuestas = Respuesta.objects.filter(examen=examen).values_list('estudiante', flat=True).distinct()
        if estudiantes_con_respuestas.exists():
            examenes_con_respuestas.append(examen)

    return render(request, 'examenes_por_calificar.html', {
        'curso': curso,
        'examenes': examenes_con_respuestas
    })
    
def seleccionar_estudiante(request, slug):
    examen = get_object_or_404(Examen, slug=slug)
    estudiantes_ids = Respuesta.objects.filter(examen=examen).values_list('estudiante', flat=True).distinct()
    estudiantes = User.objects.filter(id__in=estudiantes_ids)

    context = {
        'examen': examen,
        'estudiantes': estudiantes
    }
    return render(request, 'seleccionar_estudiante.html', context)
    
@login_required
def calificar_respuestas(request, slug, estudiante_id):
    
    examen = get_object_or_404(Examen, slug=slug)
    estudiante = get_object_or_404(User, id=estudiante_id)

    if request.user != examen.creado_por:
        return redirect('board', codigo_acceso=examen.curso.codigo_acceso)

    respuestas = Respuesta.objects.filter(examen=examen, estudiante=estudiante).select_related('pregunta')

    # Validación: si ya tiene puntaje asignado, bloquear acceso
    if respuestas.exists() and all(res.puntaje is not None for res in respuestas):
        messages.warning(request, "Este estudiante ya fue calificado para este examen.")
        return redirect('seleccionar_estudiante', slug=slug)

    if request.method == 'POST':
        for respuesta in respuestas:
            puntaje_str = request.POST.get(f'puntaje_{respuesta.id}')
            comentario = request.POST.get(f'comentario_{respuesta.id}')

            try:
                respuesta.puntaje = float(puntaje_str) if puntaje_str else None
            except ValueError:
                respuesta.puntaje = None

            respuesta.comentario = comentario
            respuesta.save()

        messages.success(request, "Calificación guardada con éxito.")
        return redirect('seleccionar_estudiante', slug=slug)
    
    return render(request, 'calificar_respuestas.html', {
        'examen': examen,
        'estudiante': estudiante,
        'respuestas': respuestas
    })
    
@login_required
@verificar_acceso_curso
def lista_retroalimentacion(request, codigo_acceso, curso):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

    if request.user.rol == 'Profesor':
        # Verificar si el docente es el creador del curso
        if curso.id_profesor != request.user:
            # Si no es el creador, tratarlo como estudiante (o mostrar mensaje)
            respuestas = Respuesta.objects.filter(
                estudiante=request.user,
                puntaje__isnull=False,
                examen__curso=curso
            ).select_related('examen')

            if not respuestas.exists():
                return render(request, 'retroalimentacion_lista.html', {
                    'mensaje': 'No hay retroalimentación disponible',
                    'codigo_acceso': codigo_acceso,
                    'es_docente': False
                })

            examenes = {}
            for respuesta in respuestas:
                examen = respuesta.examen
                examenes[examen] = examenes.get(examen, 0) + (respuesta.puntaje or 0)

            return render(request, 'retroalimentacion_lista.html', {
                'examenes': examenes,
                'codigo_acceso': codigo_acceso,
                'es_docente': False
            })

        # Si es creador, mostrar exámenes con retroalimentación pendiente
        examenes_con_retro = Examen.objects.filter(
            respuesta__puntaje__isnull=False,
            curso=curso
        ).distinct()

        return render(request, 'retroalimentacion_lista.html', {
            'examenes': examenes_con_retro,
            'codigo_acceso': codigo_acceso,
            'es_docente': True
        })

    else:
        # Para estudiantes normales
        respuestas = Respuesta.objects.filter(
            estudiante=request.user,
            puntaje__isnull=False,
            examen__curso=curso
        ).select_related('examen')

        if not respuestas.exists():
            return render(request, 'retroalimentacion_lista.html', {
                'mensaje': 'No hay retroalimentación disponible',
                'codigo_acceso': codigo_acceso,
                'es_docente': False
            })

        examenes = {}
        for respuesta in respuestas:
            examen = respuesta.examen
            examenes[examen] = examenes.get(examen, 0) + (respuesta.puntaje or 0)

        return render(request, 'retroalimentacion_lista.html', {
            'examenes': examenes,
            'codigo_acceso': codigo_acceso,
            'es_docente': False
        })
    

@login_required
def detalle_retroalimentacion(request, examen_id):
    
    respuestas = Respuesta.objects.filter(estudiante=request.user, examen_id=examen_id).select_related('pregunta')

    if not respuestas.exists():
        messages.warning(request, "No hay retroalimentación para este examen.")
        # Redirigir correctamente con el código de curso
        examen = get_object_or_404(Examen, id=examen_id)
        return redirect('lista_retroalimentacion', codigo_acceso=examen.curso.codigo_acceso)

    examen = respuestas.first().examen
    curso = examen.curso

    return render(request, 'retroalimentacion_detalle.html', {
        'respuestas': respuestas,
        'examen': examen,
        'codigo_acceso': curso.codigo_acceso
    })

@login_required
def alumnos_con_retroalimentacion(request, examen_id):
    list(get_messages(request))
    examen = get_object_or_404(Examen, id=examen_id, curso__id_profesor=request.user)

    # Obtener la suma de puntajes por estudiante
    estudiantes_con_puntaje = Respuesta.objects.filter(
        examen=examen,
        puntaje__isnull=False
    ).values(
        'estudiante__id',
        'estudiante__username',
        'estudiante__email'
    ).annotate(
        puntaje_total=Sum('puntaje')
    ).order_by('estudiante__username')

    return render(request, 'alumnos_con_retroalimentacion.html', {
        'examen': examen,
        'estudiantes': estudiantes_con_puntaje,
        'codigo_acceso': examen.curso.codigo_acceso
    })
    

@login_required
def editar_retroalimentacion(request, examen_id, estudiante_id):
    list(get_messages(request))
    
    examen = get_object_or_404(Examen, id=examen_id, curso__id_profesor=request.user)
    estudiante = get_object_or_404(User, id=estudiante_id)

    respuestas = Respuesta.objects.filter(examen=examen, estudiante=estudiante).select_related('pregunta')

    if request.method == 'POST':
        total_puntaje = 0
        for respuesta in respuestas:
            comentario = request.POST.get(f'comentario_{respuesta.id}', '').strip()
            puntaje = request.POST.get(f'puntaje_{respuesta.id}')
            try:
                puntaje = float(puntaje)
            except (ValueError, TypeError):
                puntaje = 0

            respuesta.comentario = comentario
            respuesta.puntaje = puntaje
            respuesta.save()
            total_puntaje += puntaje

        messages.success(request, "Retroalimentación actualizada con éxito.")
        return redirect('alumnos_con_retroalimentacion', examen_id=examen.id)

    return render(request, 'editar_retroalimentacion.html', {
        'examen': examen,
        'estudiante': estudiante,
        'respuestas': respuestas
    })

@login_required
def eliminar_retroalimentacion(request, examen_id, estudiante_id):
    
    examen = get_object_or_404(Examen, id=examen_id, curso__id_profesor=request.user)
    estudiante = get_object_or_404(User, id=estudiante_id)

    if request.method == 'POST':
        # Eliminar solo los puntajes y comentarios, no las respuestas en sí
        respuestas = Respuesta.objects.filter(examen=examen, estudiante=estudiante)
        for respuesta in respuestas:
            respuesta.puntaje = None
            respuesta.comentario = ''
            respuesta.save()

        messages.success(request, "Retroalimentación eliminada correctamente.")
        return redirect('alumnos_con_retroalimentacion', examen_id=examen.id)

    return render(request, 'eliminar_retroalimentacion.html', {
        'examen': examen,
        'estudiante': estudiante,
    })


# Cuarto sprint

@login_required
def enviar_actividad(request, codigo_acceso, id_actividad):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso)

    # Solo el alumno que pertenece al curso puede enviar
    if request.user == curso.id_profesor:
        return redirect('dashboard')

    if Envio.objects.filter(alumno=request.user, actividad=actividad).exists():
        messages.warning(request, "Ya enviaste esta actividad.")
        return redirect('content_detail', codigo_acceso=codigo_acceso, id_actividad=id_actividad)

    if request.method == 'POST':
        form = EnvioForm(request.POST, request.FILES)
        if form.is_valid():
            envio = form.save(commit=False)
            envio.alumno = request.user
            envio.docente = actividad.docente
            envio.curso = curso
            envio.actividad = actividad
            envio.save()
            messages.success(request, "Actividad enviada con éxito.")
            return redirect('content_detail', codigo_acceso=codigo_acceso, id_actividad=id_actividad)
    else:
        form = EnvioForm()

    return render(request, 'enviar_actividad.html', {
        'form': form,
        'actividad': actividad,
        'curso': curso,
    })


from django.utils import timezone

@login_required
def enviar_actividad(request, codigo_acceso, id_actividad):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, id=id_actividad, curso=curso)

    # Solo el alumno puede enviar
    if request.user == curso.id_profesor:
        return redirect('dashboard')

    if Envio.objects.filter(alumno=request.user, actividad=actividad).exists():
        messages.warning(request, "Ya enviaste esta actividad.")
        return redirect('content_detail', codigo_acceso=codigo_acceso, id_actividad=id_actividad)

    # Validar la fecha limite
    ahora = timezone.now()
    if actividad.fecha_limite and not actividad.permite_entrega_tardia:
        if ahora > actividad.fecha_limite:
            messages.error(request, "La fecha límite de entrega ha pasado y no se permiten entregas tardías.")
            return redirect('content_detail', codigo_acceso=codigo_acceso, id_actividad=id_actividad)

    if request.method == 'POST':
        form = EnvioForm(request.POST, request.FILES)
        if form.is_valid():
            envio = form.save(commit=False)
            envio.alumno = request.user
            envio.docente = actividad.docente
            envio.curso = curso
            envio.actividad = actividad
            envio.save()
            messages.success(request, "Actividad enviada con éxito.")
            return redirect('content_detail', codigo_acceso=codigo_acceso, id_actividad=id_actividad)
    else:
        form = EnvioForm()

    return render(request, 'enviar_actividad.html', {
        'form': form,
        'actividad': actividad,
        'curso': curso,
    })


@login_required
def listar_entregas(request, codigo_acceso, id_actividad):
    curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)
    actividad = get_object_or_404(Actividad, curso=curso, id=id_actividad)

    if request.user != curso.id_profesor:
        return redirect('dashboard')

    entregas = Envio.objects.filter(actividad=actividad)
    return render(request, 'listar_entregas.html', {
        'actividad': actividad,
        'curso': curso,
        'entregas': entregas
    })


@login_required
def calificar_entrega(request, codigo_acceso, id_envio):
    envio = get_object_or_404(Envio, id=id_envio, curso__codigo_acceso=codigo_acceso)

    if request.user != envio.docente:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CalificacionForm(request.POST, instance=envio)
        if form.is_valid():
            form.save()
            messages.success(request, "Calificación guardada con éxito.")
            return redirect('listar_entregas', codigo_acceso=codigo_acceso, id_actividad=envio.actividad.id)
    else:
        form = CalificacionForm(instance=envio)

    return render(request, 'calificar_entrega.html', {
        'form': form,
        'envio': envio
    })


# ultimo esfuerzo compañeros

def chatgpt_form(request):
    return render(request, 'chatgpt_form.html') 

@csrf_exempt
def chatgpt_prompt(request):
    if request.method == "POST":
        prompt = request.POST.get("prompt", "")

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un asistente útil."},
                    {"role": "user", "content": prompt}
                ]
            )
            reply = response.choices[0].message.content
            return JsonResponse({"response": reply})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)