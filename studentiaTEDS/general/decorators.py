from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from functools import wraps
from .models import Curso, AlumnoCurso,Examen
from django.contrib import messages


def verificar_acceso_curso(view_func):
    @wraps(view_func)
    def wrapper(request, codigo_acceso, *args, **kwargs):
        curso = get_object_or_404(Curso, codigo_acceso=codigo_acceso)

        if request.user != curso.id_profesor and not AlumnoCurso.objects.filter(curso=curso, alumno=request.user).exists():
            raise PermissionDenied("No tienes permiso para acceder a este curso.")

        # Inyectar el curso en la vista para evitar duplicarlo
        kwargs['curso'] = curso
        return view_func(request, codigo_acceso, *args, **kwargs)
    return wrapper
def verificar_acceso_examen(view_func):
    def _wrapped_view(request, slug, *args, **kwargs):
        examen = get_object_or_404(Examen, slug=slug)
        curso = examen.curso

        if request.user.rol == 'Profesor' and request.user != curso.id_profesor:
            return redirect('no_autorizado')  # o 'inicio'
        elif request.user.rol == 'Estudiante' and not curso.estudiantes.filter(id=request.user.id).exists():
            return redirect('no_autorizado')

        return view_func(request, slug, *args, **kwargs)
    return _wrapped_view

