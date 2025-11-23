from django.shortcuts import redirect
from django.contrib import messages
from .utils import usuario_es_administrador, usuario_tiene_perfil_adoptante

def administrador_requerido(view_func):
    def wrapper_func(request, *args, **kwargs):
        if usuario_es_administrador(request.user):
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('index')
    return wrapper_func

def adoptante_requerido(view_func):
    def wrapper_func(request, *args, **kwargs):
        if usuario_tiene_perfil_adoptante(request.user):
            return view_func(request, *args, **kwargs)
        elif request.user.is_authenticated:
            messages.info(request, 'Necesitas completar tu registro como adoptante.')
            return redirect('register_adopter')
        else:
            messages.info(request, 'Necesitas iniciar sesión para acceder a esta página.')
            return redirect('login')
    return wrapper_func