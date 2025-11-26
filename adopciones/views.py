from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import render_to_string
import os
from django.utils import timezone
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
        return redirect('adopciones:detalles_mascota', mascota_id=mascota_id)  # ← CORREGIDO
    
    if request.method == 'POST':
        form = FormularioSolicitudAdopcion(request.POST)
        if form.is_valid():
            solicitud_adopcion = form.save(commit=False)
            solicitud_adopcion.mascota = mascota
            solicitud_adopcion.adoptante = request.user
            solicitud_adopcion.save()
            agregar_solicitud_cola(mascota.id, solicitud_adopcion)
            
            messages.success(request, f'¡Solicitud enviada para {mascota.nombre}! Estás en la posición #{obtener_cantidad_solicitudes(mascota_id)} de la lista de espera.')
            return redirect('adopciones:catalog')  # ← CORREGIDO
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
    """Registrar información del adoptante - Solo usuarios autenticados no administradores"""
    if usuario_es_administrador(request.user):
        messages.info(request, 'Los administradores no pueden registrarse como adoptantes.')
        return redirect('adopciones:index')  # ← CORREGIDO
    
    # Verificar si ya es adoptante
    if usuario_tiene_perfil_adoptante(request.user):
        messages.info(request, 'Ya estás registrado como adoptante.')
        return redirect('adopciones:catalog')  # ← CORREGIDO
    
    if request.method == 'POST':
        form = FormularioRegistroAdoptante(request.POST)
        if form.is_valid():
            # ... tu código existente ...
            
            messages.success(request, '¡Registro completado! Ahora puedes solicitar adopciones.')
            return redirect('adopciones:catalog')  # ← CORREGIDO
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
    
    # Calcular solicitudes pendientes
    solicitudes_pendientes = 0
    for mascota in Mascota.objects.filter(disponible=True):
        solicitudes_pendientes += obtener_cantidad_solicitudes(mascota.id)
    
    # ACTIVIDAD RECIENTE - Datos dinámicos
    from datetime import datetime, timedelta
    
    # Solicitudes recientes (últimos 7 días)
    fecha_limite = timezone.now() - timedelta(days=7)
    solicitudes_recientes = SolicitudAdopcion.objects.filter(
        fecha_solicitud__gte=fecha_limite
    ).select_related('mascota', 'adoptante').order_by('-fecha_solicitud')[:5]
    
    # Mascotas agregadas recientemente
    mascotas_recientes = Mascota.objects.filter(
        fecha_creacion__gte=fecha_limite
    ).order_by('-fecha_creacion')[:3]
    
    # Adopciones concretadas recientemente
    adopciones_recientes = SolicitudAdopcion.objects.filter(
        estado='concretado',
        fecha_solicitud__gte=fecha_limite
    ).select_related('mascota', 'adoptante').order_by('-fecha_solicitud')[:3]
    
    # Estadísticas rápidas
    total_adopciones_mes = SolicitudAdopcion.objects.filter(
        estado='concretado',
        fecha_solicitud__gte=timezone.now().replace(day=1)  # Desde inicio del mes
    ).count()
    
    context = {
        'total_mascotas': total_mascotas,
        'mascotas_disponibles': mascotas_disponibles,
        'solicitudes_pendientes': solicitudes_pendientes,
        'solicitudes_recientes': solicitudes_recientes,
        'mascotas_recientes': mascotas_recientes,
        'adopciones_recientes': adopciones_recientes,
        'total_adopciones_mes': total_adopciones_mes,
        'fecha_limite': fecha_limite,
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
            return redirect('adopciones:dashboard')
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
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion in ['aceptar', 'rechazar', 'concretar']:
            # Obtener la solicitud actual SIN removerla de la cola
            solicitud_actual = ver_siguiente_solicitud(mascota_id)
            
            if not solicitud_actual:
                messages.error(request, 'No hay solicitudes para procesar.')
                return redirect('adopciones:procesar_solicitud_mascota', mascota_id=mascota_id)
            
            if accion == 'aceptar':
                solicitud_actual.estado = 'aceptado'
                solicitud_actual.save()
                messages.success(request, f'Solicitud de {solicitud_actual.adoptante.get_nombre_completo()} aceptada.')
                
            elif accion == 'rechazar':
                solicitud_actual.estado = 'rechazado'
                solicitud_actual.save()
                # Solo remover de la cola si se rechaza
                procesar_siguiente_solicitud(mascota_id)
                messages.warning(request, f'Solicitud de {solicitud_actual.adoptante.get_nombre_completo()} rechazada.')
                
            elif accion == 'concretar':
                if solicitud_actual.estado == 'aceptado':
                    try:
                        solicitud_actual.estado = 'concretado'
                        solicitud_actual.save()
                        
                        mascota.disponible = False
                        mascota.save()
                        
                        from .pdf_utils import generar_compromiso_adopcion
                        from django.core.files.base import ContentFile
                        
                        pdf_content = generar_compromiso_adopcion(solicitud_actual)
                        
                        compromiso = CompromisoAdopcion.objects.create(
                            solicitud_adopcion=solicitud_actual,
                            fecha_compromiso=timezone.now()
                        )
                        
                        nombre_archivo = f"compromiso_{solicitud_actual.id}.pdf"
                        compromiso.documento_pdf.save(nombre_archivo, ContentFile(pdf_content))
                        compromiso.save()
                        
                        # Remover de la cola solo cuando se concreta
                        procesar_siguiente_solicitud(mascota_id)
                        
                        messages.success(request, f'✅ Adopción de {mascota.nombre} concretada. PDF generado.')
                        
                    except Exception as e:
                        messages.error(request, f'❌ Error al concretar: {str(e)}')
                else:
                    messages.error(request, 'Solo se pueden concretar solicitudes aceptadas.')
        
        return redirect('adopciones:procesar_solicitud_mascota', mascota_id=mascota_id)
    
    # Para GET requests, mostrar la solicitud actual
    solicitud_actual = ver_siguiente_solicitud(mascota_id)
    
    context = {
        'mascota': mascota,
        'solicitud_actual': solicitud_actual,
        'cantidad_solicitudes': obtener_cantidad_solicitudes(mascota_id),
    }
    return render(request, 'procesar_solicitud_mascota.html', context)

@login_required
@administrador_requerido
def generate_commitment(request, solicitud_id):
    solicitud_adopcion = get_object_or_404(SolicitudAdopcion, id=solicitud_id)
    
    if solicitud_adopcion.estado != 'aceptado':
        messages.error(request, 'La solicitud debe estar aceptada para generar el compromiso.')
        return redirect('aplicacion:dashboard')
    
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
        return redirect('aplicacion:dashboard')

@login_required
@administrador_requerido
def reports(request):
    from django.utils import timezone
    from datetime import timedelta, datetime
    
    # Fechas para los reportes
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    
    # REPORTE DIARIO (hoy)
    solicitudes_hoy = SolicitudAdopcion.objects.filter(
        fecha_solicitud__date=hoy
    ).count()
    
    adopciones_hoy = SolicitudAdopcion.objects.filter(
        estado='concretado',
        fecha_solicitud__date=hoy
    ).count()
    
    mascotas_agregadas_hoy = Mascota.objects.filter(
        fecha_creacion__date=hoy
    ).count()
    
    # REPORTE SEMANAL (esta semana)
    solicitudes_semana = SolicitudAdopcion.objects.filter(
        fecha_solicitud__date__gte=inicio_semana
    ).count()
    
    adopciones_semana = SolicitudAdopcion.objects.filter(
        estado='concretado',
        fecha_solicitud__date__gte=inicio_semana
    ).count()
    
    mascotas_semana = Mascota.objects.filter(
        fecha_creacion__date__gte=inicio_semana
    ).count()
    
    # REPORTE MENSUAL (este mes)
    solicitudes_mes = SolicitudAdopcion.objects.filter(
        fecha_solicitud__date__gte=inicio_mes
    ).count()
    
    adopciones_mes = SolicitudAdopcion.objects.filter(
        estado='concretado',
        fecha_solicitud__date__gte=inicio_mes
    ).count()
    
    mascotas_mes = Mascota.objects.filter(
        fecha_creacion__date__gte=inicio_mes
    ).count()
    
    # Estadísticas generales (ya las tenías)
    total_adopciones = SolicitudAdopcion.objects.filter(estado='concretado').count()
    solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado='espera').count()
    perros = Mascota.objects.filter(tipo_mascota='perro').count()
    gatos = Mascota.objects.filter(tipo_mascota='gato').count()
    
    # Solicitudes por estado
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
        
        # Nuevos datos para reportes por período
        'reporte_diario': {
            'solicitudes': solicitudes_hoy,
            'adopciones': adopciones_hoy,
            'mascotas_agregadas': mascotas_agregadas_hoy,
            'fecha': hoy.strftime('%d/%m/%Y')
        },
        'reporte_semanal': {
            'solicitudes': solicitudes_semana,
            'adopciones': adopciones_semana,
            'mascotas_agregadas': mascotas_semana,
            'periodo': f"{inicio_semana.strftime('%d/%m')} - {hoy.strftime('%d/%m/%Y')}"
        },
        'reporte_mensual': {
            'solicitudes': solicitudes_mes,
            'adopciones': adopciones_mes,
            'mascotas_agregadas': mascotas_mes,
            'periodo': hoy.strftime('%B %Y').capitalize()
        }
    }
    return render(request, 'reporte.html', context)

@login_required
@administrador_requerido
def download_report_pdf(request):
    from django.utils import timezone
    from datetime import timedelta
    
    # Obtener la fecha actual
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())  # Lunes de esta semana
    inicio_mes = hoy.replace(day=1)  # Primer día del mes actual
    
    # Consultas básicas
    total_adopciones = SolicitudAdopcion.objects.filter(estado='concretado').count()
    solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado='espera').count()
    perros = Mascota.objects.filter(tipo_mascota='perro').count()
    gatos = Mascota.objects.filter(tipo_mascota='gato').count()
    
    # Reporte diario (hoy)
    solicitudes_hoy = SolicitudAdopcion.objects.filter(
        fecha_solicitud__date=hoy
    ).count()
    adopciones_hoy = SolicitudAdopcion.objects.filter(
        estado='concretado',
        fecha_solicitud__date=hoy
    ).count()
    mascotas_agregadas_hoy = Mascota.objects.filter(
        fecha_ingreso__date=hoy
    ).count()
    
    # Reporte semanal (esta semana)
    solicitudes_semana = SolicitudAdopcion.objects.filter(
        fecha_solicitud__date__gte=inicio_semana
    ).count()
    adopciones_semana = SolicitudAdopcion.objects.filter(
        estado='concretado',
        fecha_solicitud__date__gte=inicio_semana
    ).count()
    mascotas_semana = Mascota.objects.filter(
        fecha_ingreso__date__gte=inicio_semana
    ).count()
    
    # Reporte mensual (este mes)
    solicitudes_mes = SolicitudAdopcion.objects.filter(
        fecha_solicitud__date__gte=inicio_mes
    ).count()
    adopciones_mes = SolicitudAdopcion.objects.filter(
        estado='concretado',
        fecha_solicitud__date__gte=inicio_mes
    ).count()
    mascotas_mes = Mascota.objects.filter(
        fecha_ingreso__date__gte=inicio_mes
    ).count()
    
    datos_reporte = {
        'total_mascotas': Mascota.objects.count(),
        'mascotas_disponibles': Mascota.objects.filter(disponible=True).count(),
        'total_adopciones': total_adopciones,
        'solicitudes_pendientes': solicitudes_pendientes,
        'perros': perros,
        'gatos': gatos,
        
        # Agregar los nuevos reportes
        'reporte_diario': {
            'solicitudes': solicitudes_hoy,
            'adopciones': adopciones_hoy,
            'mascotas_agregadas': mascotas_agregadas_hoy,
        },
        'reporte_semanal': {
            'solicitudes': solicitudes_semana,
            'adopciones': adopciones_semana,
            'mascotas_agregadas': mascotas_semana,
        },
        'reporte_mensual': {
            'solicitudes': solicitudes_mes,
            'adopciones': adopciones_mes,
            'mascotas_agregadas': mascotas_mes,
        }
    }
    
    try:
        # Usar TU función de PDF
        from .pdf_utils import generar_reporte_adopciones
        pdf_content = generar_reporte_adopciones(datos_reporte)
        
        respuesta = HttpResponse(pdf_content, content_type='application/pdf')
        respuesta['Content-Disposition'] = 'attachment; filename="reporte_adopciones.pdf"'
        
        messages.success(request, 'Reporte generado exitosamente.')
        return respuesta
        
    except Exception as e:
        messages.error(request, f'Error al generar el reporte: {e}')
        return redirect('adopciones:reports')

@login_required
@administrador_requerido
def editar_mascota(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    
    if not mascota.puede_ser_editada():
        messages.error(request, 'No se puede editar esta mascota porque tiene solicitudes de adopción aceptadas o concretadas.')
        return redirect('adopciones:listar_mascotas')
    
    if request.method == 'POST':
        form = FormularioMascota(request.POST, request.FILES, instance=mascota)
        if form.is_valid():
            mascota_editada = form.save()
            
            # Actualizar en el árbol
            from .utils import arbol_mascotas
            # Primero eliminar la antigua
            arbol_mascotas.eliminar(mascota)
            # Luego insertar la editada
            arbol_mascotas.insertar(mascota_editada)
            
            messages.success(request, f'Mascota "{mascota_editada.nombre}" actualizada exitosamente.')
            return redirect('adopciones:listar_mascotas')
    else:
        form = FormularioMascota(instance=mascota)
    
    return render(request, 'editar_mascota.html', {
        'form': form,
        'mascota': mascota
    })

@login_required
@administrador_requerido
def eliminar_mascota(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    
    if not mascota.puede_ser_eliminada():
        messages.error(request, 'No se puede eliminar esta mascota porque tiene solicitudes de adopción asociadas.')
        return redirect('adopciones:listar_mascotas')
    
    if request.method == 'POST':
        nombre_mascota = mascota.nombre
        
        from .utils import arbol_mascotas
        arbol_mascotas.eliminar(mascota)
        
        mascota.delete()
        
        messages.success(request, f'Mascota "{nombre_mascota}" eliminada exitosamente.')
        return redirect('adopciones:listar_mascotas')
    
    return render(request, 'eliminar_mascota.html', {
        'mascota': mascota
    })

@login_required
@administrador_requerido
def listar_mascotas(request):
    mascotas = Mascota.objects.all().order_by('-fecha_creacion')
    
    return render(request, 'listar_mascotas.html', {
        'mascotas': mascotas
    })

from django.contrib.auth import logout
from django.shortcuts import redirect


def custom_logout(request):
    """Vista de logout que acepta tanto GET como POST"""
    if request.method in ['GET', 'POST']:
        logout(request)
        return redirect('/')
    return redirect('/')

from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from .forms import FormularioRegistroUsuario  

def registrar_usuario(request):
    if request.method == 'POST':
        form = FormularioRegistroUsuario(request.POST)
        if form.is_valid():
            usuario = form.save()
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            usuario = authenticate(email=email, password=password)
            
            if usuario is not None:
                login(request, usuario)
                messages.success(request, '¡Registro exitoso! Bienvenido/a.')
                

                if usuario.es_administrador:
                    return redirect('adopciones:dashboard')
                else:
                    return redirect('adopciones:catalog')
                    
    else:
        form = FormularioRegistroUsuario()
    
    return render(request, 'registrar_usuario.html', {'form': form})

@login_required
def mis_solicitudes(request):
    solicitudes = SolicitudAdopcion.objects.filter(adoptante=request.user).order_by('-fecha_solicitud')
    
    context = {
        'solicitudes': solicitudes,
    }
    return render(request, 'mis_solicitudes.html', context)

@login_required
@administrador_requerido
def concretar_adopciones_aceptadas(request):
    """Vista especial para concretar adopciones ya aceptadas"""
    # Buscar solicitudes aceptadas donde la mascota aún esté disponible
    solicitudes_aceptadas = SolicitudAdopcion.objects.filter(
        estado='aceptado',
        mascota__disponible=True
    ).select_related('mascota', 'adoptante').order_by('fecha_solicitud')
    
    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        solicitud = get_object_or_404(SolicitudAdopcion, id=solicitud_id)
        
        if solicitud.estado == 'aceptado':
            try:
                # 1. Cambiar estado a concretado
                solicitud.estado = 'concretado'
                solicitud.save()
                
                # 2. Marcar mascota como no disponible
                mascota = solicitud.mascota
                mascota.disponible = False
                mascota.save()
                
                # 3. Generar PDF del compromiso
                from .pdf_utils import generar_compromiso_adopcion
                from django.core.files.base import ContentFile
                
                pdf_content = generar_compromiso_adopcion(solicitud)
                
                # 4. Crear y guardar el compromiso
                compromiso = CompromisoAdopcion.objects.create(
                    solicitud_adopcion=solicitud,
                    fecha_compromiso=timezone.now()
                )
                
                nombre_archivo = f"compromiso_{solicitud.id}.pdf"
                compromiso.documento_pdf.save(nombre_archivo, ContentFile(pdf_content))
                compromiso.save()
                
                messages.success(request, f'✅ Adopción de {mascota.nombre} concretada exitosamente. PDF generado.')
                
            except Exception as e:
                messages.error(request, f'❌ Error al concretar adopción: {str(e)}')
        else:
            messages.error(request, 'Esta solicitud no está en estado aceptado.')
        
        return redirect('adopciones:concretar_adopciones_aceptadas')
    
    context = {
        'solicitudes_aceptadas': solicitudes_aceptadas,
    }
    return render(request, 'concretar_adopciones_aceptadas.html', context)