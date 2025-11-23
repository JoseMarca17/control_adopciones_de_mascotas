from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
import os
from .models import Mascota, PerfilAdoptante, SolicitudAdopcion, CompromisoAdopcion
from .forms import FormularioMascota, FormularioSolicitudAdopcion, FormularioRegistroAdoptante
from .utils import (
    obtener_mascotas_ordenadas, 
    agregar_solicitud_cola,
    procesar_siguiente_solicitud,
    ver_siguiente_solicitud,
    obtener_cantidad_solicitudes,
    usuario_es_administrador,
    usuario_tiene_perfil_adoptante
)
from .decorators import administrador_requerido, adoptante_requerido
from .pdf_utils import generar_compromiso_adopcion, generar_reporte_adopciones
from datetime import date

def index(request):
    return render(request, 'index.html')

def catalog(request):
    mascotas = obtener_mascotas_ordenadas()
    context = {
        'mascotas': mascotas,
    }
    return render(request, 'catalog.html', context)

def detalles_mascota(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    cantidad_solicitudes = obtener_cantidad_solicitudes(mascota_id)
    
    context = {
        'mascota': mascota,
        'cantidad_solicitudes': cantidad_solicitudes,
        'puede_adoptar': usuario_tiene_perfil_adoptante(request.user),
    }
    return render(request, 'detalle_mascota.html', context)

@login_required
@adoptante_requerido
def solicitud_adopcion(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    solicitud_existente = SolicitudAdopcion.objects.filter(
        mascota=mascota, 
        adoptante=request.user,
        estado__in=['espera', 'aceptado']
    ).exists()
    
    if solicitud_existente:
        messages.warning(request, 'Ya tienes una solicitud pendiente o aceptada para esta mascota.')
        return redirect('detalle_mascota', mascota_id=mascota_id)
    
    if request.method == 'POST':
        form = FormularioSolicitudAdopcion(request.POST)
        if form.is_valid():
            solicitud_adopcion = form.save(commit=False)
            solicitud_adopcion.mascota = mascota
            solicitud_adopcion.adoptante = request.user
            solicitud_adopcion.save()
            agregar_solicitud_cola(mascota.id, solicitud_adopcion)
            
            messages.success(request, f'¡Solicitud enviada para {mascota.nombre}! Estás en la posición #{obtener_cantidad_solicitudes(mascota_id)} de la lista de espera.')
            return redirect('catalog')
    else:
        form = FormularioSolicitudAdopcion()
    
    context = {
        'form': form,
        'mascota': mascota,
        'cantidad_solicitudes': obtener_cantidad_solicitudes(mascota_id),
    }
    return render(request, 'solicitud_adopcion.html', context)

@login_required
def registrar_adoptante(request):
    if usuario_es_administrador(request.user):
        messages.info(request, 'Los administradores no pueden registrarse como adoptantes.')
        return redirect('index')
    
    if usuario_tiene_perfil_adoptante(request.user):
        messages.info(request, 'Ya estás registrado como adoptante.')
        return redirect('catalog')
    
    if request.method == 'POST':
        form = FormularioRegistroAdoptante(request.POST)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.telefono = form.cleaned_data['telefono']
            request.user.direccion = form.cleaned_data['direccion']
            request.user.save()
            
            perfil_adoptante = PerfilAdoptante(
                usuario=request.user,
                numero_identificacion=form.cleaned_data['numero_identificacion'],
                ocupacion=form.cleaned_data['ocupacion'],
                experiencia_mascotas=form.cleaned_data['experiencia_mascotas'],
                tipo_vivienda=form.cleaned_data['tipo_vivienda'],
                tiene_patio=form.cleaned_data['tiene_patio'],
                otras_mascotas=form.cleaned_data['otras_mascotas']
            )
            perfil_adoptante.save()
            
            messages.success(request, '¡Registro completado! Ahora puedes solicitar adopciones.')
            return redirect('catalog')
    else:
        form = FormularioRegistroAdoptante(initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name
        })
    
    return render(request, 'registrar_adoptante.html', {'form': form})

@login_required
@administrador_requerido
def dashboard(request):
    total_mascotas = Mascota.objects.count()
    mascotas_disponibles = Mascota.objects.filter(disponible=True).count()
    
    solicitudes_pendientes = 0
    for mascota in Mascota.objects.filter(disponible=True):
        solicitudes_pendientes += obtener_cantidad_solicitudes(mascota.id)
    
    context = {
        'total_mascotas': total_mascotas,
        'mascotas_disponibles': mascotas_disponibles,
        'solicitudes_pendientes': solicitudes_pendientes,
    }
    return render(request, 'dashboard.html', context)

@login_required
@administrador_requerido
def agregar_mascota(request):
    if request.method == 'POST':
        form = FormularioMascota(request.POST, request.FILES)
        if form.is_valid():
            mascota = form.save()
            
            from .utils import arbol_mascotas
            arbol_mascotas.insertar(mascota)
            
            messages.success(request, f'Mascota "{mascota.nombre}" agregada exitosamente.')
            return redirect('dashboard')
    else:
        form = FormularioMascota()
    
    return render(request, 'agregar_mascota.html', {'form': form})

@login_required
@administrador_requerido
def procesar_solicitud(request):
    mascotas_con_solicitudes = []
    
    for mascota in Mascota.objects.filter(disponible=True):
        cantidad = obtener_cantidad_solicitudes(mascota.id)
        if cantidad > 0:
            mascotas_con_solicitudes.append({
                'mascota': mascota,
                'cantidad_solicitudes': cantidad,
                'siguiente_solicitud': ver_siguiente_solicitud(mascota.id)
            })
    
    context = {
        'mascotas_con_solicitudes': mascotas_con_solicitudes,
    }
    return render(request, 'procesar_solicitud.html', context)

@login_required
@administrador_requerido
def procesar_solicitud_mascota(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    solicitud_actual = ver_siguiente_solicitud(mascota_id)
    
    if request.method == 'POST' and solicitud_actual:
        accion = request.POST.get('accion')
        solicitud_procesada = procesar_siguiente_solicitud(mascota_id)
        
        if accion == 'aceptar':
            solicitud_procesada.estado = 'aceptado'
            solicitud_procesada.save()
            messages.success(request, f'Solicitud de {solicitud_procesada.adoptante.get_nombre_completo()} aceptada.')
        elif accion == 'rechazar':
            solicitud_procesada.estado = 'rechazado'
            solicitud_procesada.save()
            messages.warning(request, f'Solicitud de {solicitud_procesada.adoptante.get_nombre_completo()} rechazada.')
        
        return redirect('procesar_solicitud_mascota', mascota_id=mascota_id)
    
    context = {
        'mascota': mascota,
        'solicitud_actual': solicitud_actual,
        'cantidad_solicitudes': obtener_cantidad_solicitudes(mascota_id),
    }
    return render(request, 'processr_solicitud_mascota.html', context)

@login_required
@administrador_requerido
def generate_commitment(request, solicitud_id):
    solicitud_adopcion = get_object_or_404(SolicitudAdopcion, id=solicitud_id)
    
    if solicitud_adopcion.estado != 'aceptado':
        messages.error(request, 'La solicitud debe estar aceptada para generar el compromiso.')
        return redirect('dashboard')
    
    try:
        pdf_content = generar_compromiso_adopcion(solicitud_adopcion)

        respuesta = HttpResponse(pdf_content, content_type='application/pdf')
        respuesta['Content-Disposition'] = f'attachment; filename="compromiso_{solicitud_adopcion.id}.pdf"'

        solicitud_adopcion.estado = 'concretado'
        solicitud_adopcion.save()

        from django.core.files.base import ContentFile
        compromiso = CompromisoAdopcion(solicitud_adopcion=solicitud_adopcion)
        compromiso.documento_pdf.save(f'compromiso_{solicitud_adopcion.id}.pdf', ContentFile(pdf_content))
        compromiso.save()
        
        messages.success(request, 'Compromiso de adopción generado exitosamente.')
        return respuesta
        
    except Exception as e:
        messages.error(request, f'Error al generar el PDF: {e}')
        return redirect('dashboard')

@login_required
@administrador_requerido
def reports(request):
    total_adopciones = SolicitudAdopcion.objects.filter(estado='concretado').count()
    solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado='espera').count()

    perros = Mascota.objects.filter(tipo_mascota='perro').count()
    gatos = Mascota.objects.filter(tipo_mascota='gato').count()

    solicitudes_por_estado = []
    for estado in ['espera', 'aceptado', 'rechazado', 'concretado']:
        count = SolicitudAdopcion.objects.filter(estado=estado).count()
        solicitudes_por_estado.append({
            'estado': estado,
            'count': count
        })
    
    context = {
        'total_adopciones': total_adopciones,
        'solicitudes_pendientes': solicitudes_pendientes,
        'perros': perros,
        'gatos': gatos,
        'solicitudes_por_estado': solicitudes_por_estado,
    }
    return render(request, 'reporte.html', context)

@login_required
@administrador_requerido
def download_report_pdf(request):
    total_adopciones = SolicitudAdopcion.objects.filter(estado='concretado').count()
    solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado='espera').count()
    perros = Mascota.objects.filter(tipo_mascota='perro').count()
    gatos = Mascota.objects.filter(tipo_mascota='gato').count()
    
    datos_reporte = {
        'total_mascotas': Mascota.objects.count(),
        'mascotas_disponibles': Mascota.objects.filter(disponible=True).count(),
        'total_adopciones': total_adopciones,
        'solicitudes_pendientes': solicitudes_pendientes,
        'perros': perros,
        'gatos': gatos,
    }
    
    try:
        pdf_content = generar_reporte_adopciones(datos_reporte)
        
        respuesta = HttpResponse(pdf_content, content_type='application/pdf')
        respuesta['Content-Disposition'] = 'attachment; filename="reporte_adopciones.pdf"'
        
        messages.success(request, 'Reporte generado exitosamente.')
        return respuesta
        
    except Exception as e:
        messages.error(request, f'Error al generar el reporte: {e}')
        return redirect('reports')