from django.shortcuts import render

# Create your views here.
"""
Vistas para la aplicación de adopciones.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
from .models import Mascota, Adoptante, SolicitudAdopcion, CompromisoAdopcion
from .forms import FormularioMascota, FormularioSolicitudAdopcion, FormularioRegistroAdoptante
from .utils import (
    obtener_mascotas_ordenadas, 
    agregar_solicitud_cola,
    procesar_siguiente_solicitud,
    ver_siguiente_solicitud,
    obtener_cantidad_solicitudes,
    inicializar_estructuras
)
from datetime import fecha

def es_administrador(usuario):
    """Verificar si el usuario es administrador"""
    return usuario.groups.filter(name='Administrador').exists()

def pagina_inicio(peticion):
    """Página principal del sitio"""
    return render(peticion, 'inicio.html')

def catalogo(peticion):
    """Página del catálogo de mascotas"""
    mascotas = obtener_mascotas_ordenadas()
    return render(peticion, 'catalogo.html', {'mascotas': mascotas})

def detalle_mascota(peticion, mascota_id):
    """Página de detalles de una mascota"""
    mascota = get_object_or_404(Mascota, id=mascota_id)
    cantidad_solicitudes = obtener_cantidad_solicitudes(mascota_id)
    
    contexto = {
        'mascota': mascota,
        'cantidad_solicitudes': cantidad_solicitudes,
    }
    return render(peticion, 'detalle_mascota.html', contexto)

@login_required
def solicitar_adopcion(peticion, mascota_id):
    """Solicitar adopción de una mascota"""
    mascota = get_object_or_404(Mascota, id=mascota_id)
    
    # Verificar si el usuario es un adoptante registrado
    try:
        adoptante = Adoptante.objects.get(usuario=peticion.user)
    except Adoptante.DoesNotExist:
        return redirect('registrar_adoptante')
    
    if peticion.method == 'POST':
        formulario = FormularioSolicitudAdopcion(peticion.POST)
        if formulario.is_valid():
            solicitud_adopcion = formulario.save(commit=False)
            solicitud_adopcion.mascota = mascota
            solicitud_adopcion.adoptante = adoptante
            solicitud_adopcion.save()
            
            # Agregar a la cola correspondiente
            agregar_solicitud_cola(mascota.id, solicitud_adopcion)
            
            return redirect('catalogo')
    else:
        formulario = FormularioSolicitudAdopcion()
    
    contexto = {
        'formulario': formulario,
        'mascota': mascota,
        'cantidad_solicitudes': obtener_cantidad_solicitudes(mascota_id),
    }
    return render(peticion, 'solicitud_adopcion.html', contexto)

@login_required
def registrar_adoptante(peticion):
    """Registrar información del adoptante"""
    if peticion.method == 'POST':
        formulario = FormularioRegistroAdoptante(peticion.POST)
        if formulario.is_valid():
            usuario = peticion.user
            usuario.first_name = formulario.cleaned_data['first_name']
            usuario.last_name = formulario.cleaned_data['last_name']
            usuario.save()
            
            adoptante = Adoptante(
                usuario=usuario,
                telefono=formulario.cleaned_data['telefono'],
                direccion=formulario.cleaned_data['direccion'],
                numero_identificacion=formulario.cleaned_data['numero_identificacion']
            )
            adoptante.save()
            
            return redirect('catalogo')
    else:
        formulario = FormularioRegistroAdoptante()
    
    return render(peticion, 'registrar_adoptante.html', {'formulario': formulario})

@login_required
@user_passes_test(es_administrador)
def panel_administracion(peticion):
    """Panel de administración"""
    # Obtener estadísticas
    total_mascotas = Mascota.objects.count()
    mascotas_disponibles = Mascota.objects.filter(disponible=True).count()
    
    # Calcular solicitudes pendientes totales
    solicitudes_pendientes = 0
    for mascota in Mascota.objects.filter(disponible=True):
        solicitudes_pendientes += obtener_cantidad_solicitudes(mascota.id)
    
    contexto = {
        'total_mascotas': total_mascotas,
        'mascotas_disponibles': mascotas_disponibles,
        'solicitudes_pendientes': solicitudes_pendientes,
    }
    return render(peticion, 'panel_administracion.html', contexto)

@login_required
@user_passes_test(es_administrador)
def agregar_mascota(peticion):
    """Agregar nueva mascota"""
    if peticion.method == 'POST':
        formulario = FormularioMascota(peticion.POST, peticion.FILES)
        if formulario.is_valid():
            mascota = formulario.save()
            
            # Agregar al árbol
            from .utils import arbol_mascotas
            arbol_mascotas.insertar(mascota)
            
            return redirect('panel_administracion')
    else:
        formulario = FormularioMascota()
    
    return render(peticion, 'agregar_mascota.html', {'formulario': formulario})

@login_required
@user_passes_test(es_administrador)
def procesar_solicitudes(peticion):
    """Procesar solicitudes de adopción"""
    mascotas_con_solicitudes = []
    
    for mascota in Mascota.objects.filter(disponible=True):
        cantidad = obtener_cantidad_solicitudes(mascota.id)
        if cantidad > 0:
            mascotas_con_solicitudes.append({
                'mascota': mascota,
                'cantidad_solicitudes': cantidad,
                'siguiente_solicitud': ver_siguiente_solicitud(mascota.id)
            })
    
    contexto = {
        'mascotas_con_solicitudes': mascotas_con_solicitudes,
    }
    return render(peticion, 'procesar_solicitudes.html', contexto)

@login_required
@user_passes_test(es_administrador)
def procesar_solicitud_mascota(peticion, mascota_id):
    """Procesar solicitudes específicas de una mascota"""
    mascota = get_object_or_404(Mascota, id=mascota_id)
    solicitud_actual = ver_siguiente_solicitud(mascota_id)
    
    if peticion.method == 'POST' and solicitud_actual:
        accion = peticion.POST.get('accion')
        solicitud_procesada = procesar_siguiente_solicitud(mascota_id)
        
        if accion == 'aceptar':
            solicitud_procesada.estado = 'aceptado'
            solicitud_procesada.save()
        elif accion == 'rechazar':
            solicitud_procesada.estado = 'rechazado'
            solicitud_procesada.save()
        
        return redirect('procesar_solicitud_mascota', mascota_id=mascota_id)
    
    contexto = {
        'mascota': mascota,
        'solicitud_actual': solicitud_actual,
        'cantidad_solicitudes': obtener_cantidad_solicitudes(mascota_id),
    }
    return render(peticion, 'procesar_solicitud_mascota.html', contexto)

@login_required
@user_passes_test(es_administrador)
def generar_compromiso(peticion, solicitud_id):
    """Generar PDF de compromiso de adopción"""
    solicitud_adopcion = get_object_or_404(SolicitudAdopcion, id=solicitud_id)
    
    if solicitud_adopcion.estado != 'aceptado':
        return redirect('panel_administracion')
    
    # Generar PDF
    html_string = render_to_string('compromiso_pdf.html', {
        'solicitud_adopcion': solicitud_adopcion,
        'hoy': fecha.today()
    })
    
    html = HTML(string=html_string)
    resultado = html.write_pdf()
    
    # Crear respuesta PDF
    respuesta = HttpResponse(resultado, content_type='application/pdf')
    respuesta['Content-Disposition'] = f'attachment; filename="compromiso_{solicitud_adopcion.id}.pdf"'
    
    # Actualizar estado
    solicitud_adopcion.estado = 'concretado'
    solicitud_adopcion.save()
    
    # Crear registro del compromiso
    from django.core.files.base import ContentFile
    compromiso = CompromisoAdopcion(solicitud_adopcion=solicitud_adopcion)
    compromiso.documento_pdf.save(f'compromiso_{solicitud_adopcion.id}.pdf', ContentFile(resultado))
    compromiso.save()
    
    return respuesta

@login_required
@user_passes_test(es_administrador)
def reportes(peticion):
    """Página de reportes"""
    total_adopciones = SolicitudAdopcion.objects.filter(estado='concretado').count()
    solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado='espera').count()
    
    # Mascotas por tipo
    perros = Mascota.objects.filter(tipo_mascota='perro').count()
    gatos = Mascota.objects.filter(tipo_mascota='gato').count()
    
    contexto = {
        'total_adopciones': total_adopciones,
        'solicitudes_pendientes': solicitudes_pendientes,
        'perros': perros,
        'gatos': gatos,
    }
    return render(peticion, 'reportes.html', contexto)

# Inicializar estructuras al cargar el módulo
inicializar_estructuras()