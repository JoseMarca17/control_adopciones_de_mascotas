from .utils import usuario_es_administrador, usuario_tiene_perfil_adoptante

def info_usuario(request):
    context = {
        'usuario_autenticado': request.user.is_authenticated,
        'usuario_es_administrador': False,
        'usuario_tiene_perfil_adoptante': False,
    }
    
    if request.user.is_authenticated:
        context.update({
            'usuario_es_administrador': usuario_es_administrador(request.user),
            'usuario_tiene_perfil_adoptante': usuario_tiene_perfil_adoptante(request.user),
        })
    
    return context