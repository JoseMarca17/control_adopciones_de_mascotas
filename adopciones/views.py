from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import logout, login, authenticate

from .models import Mascota, PerfilAdoptante, SolicitudAdopcion, CompromisoAdopcion, Usuario
from .forms import (
    FormularioMascota, 
    FormularioSolicitudAdopcion, 
    FormularioRegistroAdoptante,
    FormularioRegistroUsuario,
    FormularioCrearAdministrador,
    FormularioCambiarPasswordAdmin,
    FormularioEditarAdministrador
)
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

def index(request):
    return render(request, 'index.html')

def catalog(request):
    mascotas = obtener_mascotas_ordenadas()
    context = {'mascotas': mascotas}
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
        return redirect('adopciones:detalles_mascota', mascota_id=mascota_id)
    
    if request.method == 'POST':
        form = FormularioSolicitudAdopcion(request.POST)
        if form.is_valid():
            solicitud_adopcion = form.save(commit=False)
            solicitud_adopcion.mascota = mascota
            solicitud_adopcion.adoptante = request.user
            solicitud_adopcion.save()
            agregar_solicitud_cola(mascota.id, solicitud_adopcion)
            
            messages.success(request, f'¡Solicitud enviada para {mascota.nombre}!')
            return redirect('adopciones:catalog')
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
        return redirect('adopciones:index')
    
    if usuario_tiene_perfil_adoptante(request.user):
        messages.info(request, 'Ya estás registrado como adoptante.')
        return redirect('adopciones:catalog')
    
    if request.method == 'POST':
        form = FormularioRegistroAdoptante(request.POST)
        if form.is_valid():
            usuario = request.user
            usuario.first_name = form.cleaned_data['first_name']
            usuario.last_name = form.cleaned_data['last_name']
            usuario.telefono = form.cleaned_data['telefono']
            usuario.direccion = form.cleaned_data['direccion']
            usuario.save()
            
            PerfilAdoptante.objects.create(
                usuario=usuario,
                numero_identificacion=form.cleaned_data['numero_identificacion'],
                ocupacion=form.cleaned_data['ocupacion'],
                experiencia_mascotas=form.cleaned_data['experiencia_mascotas'],
                tipo_vivienda=form.cleaned_data['tipo_vivienda'],
                tiene_patio=form.cleaned_data['tiene_patio'],
                otras_mascotas=form.cleaned_data['otras_mascotas']
            )
            
            messages.success(request, '¡Registro completado!')
            return redirect('adopciones:catalog')
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
    
    fecha_limite = timezone.now() - timedelta(days=7)
    solicitudes_recientes = SolicitudAdopcion.objects.filter(
        fecha_solicitud__gte=fecha_limite
    ).select_related('mascota', 'adoptante').order_by('-fecha_solicitud')[:5]
    
    mascotas_recientes = Mascota.objects.filter(
        fecha_creacion__gte=fecha_limite
    ).order_by('-fecha_creacion')[:3]
    
    adopciones_recientes = SolicitudAdopcion.objects.filter(
        estado='concretado',
        fecha_solicitud__gte=fecha_limite
    ).select_related('mascota', 'adoptante').order_by('-fecha_solicitud')[:3]
    
    total_adopciones_mes = SolicitudAdopcion.objects.filter(
        estado='concretado',
        fecha_solicitud__gte=timezone.now().replace(day=1)
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
    
    context = {'mascotas_con_solicitudes': mascotas_con_solicitudes}
    return render(request, 'procesar_solicitud.html', context)

@login_required
@administrador_requerido
def procesar_solicitud_mascota(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion in ['aceptar', 'rechazar', 'concretar']:
            solicitud_actual = ver_siguiente_solicitud(mascota_id)
            
            if not solicitud_actual:
                messages.error(request, 'No hay solicitudes para procesar.')
                return redirect('adopciones:procesar_solicitud_mascota', mascota_id=mascota_id)
            
            if accion == 'aceptar':
                solicitud_actual.estado = 'aceptado'
                solicitud_actual.save()
                messages.success(request, f'Solicitud aceptada.')
                
            elif accion == 'rechazar':
                solicitud_actual.estado = 'rechazado'
                solicitud_actual.save()
                procesar_siguiente_solicitud(mascota_id)
                messages.warning(request, f'Solicitud rechazada.')
                
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
                        
                        procesar_siguiente_solicitud(mascota_id)
                        
                        messages.success(request, f'✅ Adopción concretada.')
                        
                    except Exception as e:
                        messages.error(request, f'❌ Error al concretar: {str(e)}')
                else:
                    messages.error(request, 'Solo se pueden concretar solicitudes aceptadas.')
        
        return redirect('adopciones:procesar_solicitud_mascota', mascota_id=mascota_id)
    
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
        return redirect('adopciones:dashboard')
    
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
        return redirect('adopciones:dashboard')

@login_required
@administrador_requerido
def reports(request):
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    
    solicitudes_hoy = SolicitudAdopcion.objects.filter(fecha_solicitud__date=hoy).count()
    adopciones_hoy = SolicitudAdopcion.objects.filter(estado='concretado', fecha_solicitud__date=hoy).count()
    mascotas_agregadas_hoy = Mascota.objects.filter(fecha_creacion__date=hoy).count()
    
    solicitudes_semana = SolicitudAdopcion.objects.filter(fecha_solicitud__date__gte=inicio_semana).count()
    adopciones_semana = SolicitudAdopcion.objects.filter(estado='concretado', fecha_solicitud__date__gte=inicio_semana).count()
    mascotas_semana = Mascota.objects.filter(fecha_creacion__date__gte=inicio_semana).count()
    
    solicitudes_mes = SolicitudAdopcion.objects.filter(fecha_solicitud__date__gte=inicio_mes).count()
    adopciones_mes = SolicitudAdopcion.objects.filter(estado='concretado', fecha_solicitud__date__gte=inicio_mes).count()
    mascotas_mes = Mascota.objects.filter(fecha_creacion__date__gte=inicio_mes).count()
    
    total_adopciones = SolicitudAdopcion.objects.filter(estado='concretado').count()
    solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado='espera').count()
    perros = Mascota.objects.filter(tipo_mascota='perro').count()
    gatos = Mascota.objects.filter(tipo_mascota='gato').count()
    
    solicitudes_por_estado = []
    for estado in ['espera', 'aceptado', 'rechazado', 'concretado']:
        count = SolicitudAdopcion.objects.filter(estado=estado).count()
        solicitudes_por_estado.append({'estado': estado, 'count': count})
    
    todas_solicitudes = SolicitudAdopcion.objects.select_related('adoptante', 'mascota').order_by('-fecha_solicitud')
    
    context = {
        'total_adopciones': total_adopciones,
        'solicitudes_pendientes': solicitudes_pendientes,
        'perros': perros,
        'gatos': gatos,
        'solicitudes_por_estado': solicitudes_por_estado,
        'total_solicitudes': todas_solicitudes.count(),
        'solicitudes': todas_solicitudes,
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
    hoy = timezone.now().date()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)
    
    total_adopciones = SolicitudAdopcion.objects.filter(estado='concretado').count()
    solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado='espera').count()
    perros = Mascota.objects.filter(tipo_mascota='perro').count()
    gatos = Mascota.objects.filter(tipo_mascota='gato').count()
    
    solicitudes_hoy = SolicitudAdopcion.objects.filter(fecha_solicitud__date=hoy).count()
    adopciones_hoy = SolicitudAdopcion.objects.filter(estado='concretado', fecha_solicitud__date=hoy).count()
    mascotas_agregadas_hoy = Mascota.objects.filter(fecha_ingreso__date=hoy).count()
    
    solicitudes_semana = SolicitudAdopcion.objects.filter(fecha_solicitud__date__gte=inicio_semana).count()
    adopciones_semana = SolicitudAdopcion.objects.filter(estado='concretado', fecha_solicitud__date__gte=inicio_semana).count()
    mascotas_semana = Mascota.objects.filter(fecha_ingreso__date__gte=inicio_semana).count()
    
    solicitudes_mes = SolicitudAdopcion.objects.filter(fecha_solicitud__date__gte=inicio_mes).count()
    adopciones_mes = SolicitudAdopcion.objects.filter(estado='concretado', fecha_solicitud__date__gte=inicio_mes).count()
    mascotas_mes = Mascota.objects.filter(fecha_ingreso__date__gte=inicio_mes).count()
    
    datos_reporte = {
        'total_mascotas': Mascota.objects.count(),
        'mascotas_disponibles': Mascota.objects.filter(disponible=True).count(),
        'total_adopciones': total_adopciones,
        'solicitudes_pendientes': solicitudes_pendientes,
        'perros': perros,
        'gatos': gatos,
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
        messages.error(request, 'No se puede editar esta mascota.')
        return redirect('adopciones:listar_mascotas')
    
    if request.method == 'POST':
        form = FormularioMascota(request.POST, request.FILES, instance=mascota)
        if form.is_valid():
            mascota_editada = form.save()
            
            from .utils import arbol_mascotas
            arbol_mascotas.eliminar(mascota)
            arbol_mascotas.insertar(mascota_editada)
            
            messages.success(request, f'Mascota "{mascota_editada.nombre}" actualizada exitosamente.')
            return redirect('adopciones:listar_mascotas')
    else:
        form = FormularioMascota(instance=mascota)
    
    return render(request, 'editar_mascota.html', {'form': form, 'mascota': mascota})

@login_required
@administrador_requerido
def eliminar_mascota(request, mascota_id):
    mascota = get_object_or_404(Mascota, id=mascota_id)
    
    if not mascota.puede_ser_eliminada():
        messages.error(request, 'No se puede eliminar esta mascota.')
        return redirect('adopciones:listar_mascotas')
    
    if request.method == 'POST':
        nombre_mascota = mascota.nombre
        
        from .utils import arbol_mascotas
        arbol_mascotas.eliminar(mascota)
        mascota.delete()
        
        messages.success(request, f'Mascota "{nombre_mascota}" eliminada exitosamente.')
        return redirect('adopciones:listar_mascotas')
    
    return render(request, 'eliminar_mascota.html', {'mascota': mascota})

@login_required
@administrador_requerido
def listar_mascotas(request):
    mascotas = Mascota.objects.all().order_by('-fecha_creacion')
    return render(request, 'listar_mascotas.html', {'mascotas': mascotas})

def custom_logout(request):
    if request.method in ['GET', 'POST']:
        logout(request)
        return redirect('/')
    return redirect('/')

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
    return render(request, 'mis_solicitudes.html', {'solicitudes': solicitudes})

@login_required
@administrador_requerido
def concretar_adopciones_aceptadas(request):
    solicitudes_aceptadas = SolicitudAdopcion.objects.filter(
        estado='aceptado',
        mascota__disponible=True
    ).select_related('mascota', 'adoptante').order_by('fecha_solicitud')
    
    if request.method == 'POST':
        solicitud_id = request.POST.get('solicitud_id')
        solicitud = get_object_or_404(SolicitudAdopcion, id=solicitud_id)
        
        if solicitud.estado == 'aceptado':
            try:
                solicitud.estado = 'concretado'
                solicitud.save()
                
                mascota = solicitud.mascota
                mascota.disponible = False
                mascota.save()
                
                from .pdf_utils import generar_compromiso_adopcion
                from django.core.files.base import ContentFile
                
                pdf_content = generar_compromiso_adopcion(solicitud)
                
                compromiso = CompromisoAdopcion.objects.create(
                    solicitud_adopcion=solicitud,
                    fecha_compromiso=timezone.now()
                )
                
                nombre_archivo = f"compromiso_{solicitud.id}.pdf"
                compromiso.documento_pdf.save(nombre_archivo, ContentFile(pdf_content))
                compromiso.save()
                
                messages.success(request, f'✅ Adopción concretada.')
                
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
        else:
            messages.error(request, 'Esta solicitud no está en estado aceptado.')
        
        return redirect('adopciones:concretar_adopciones_aceptadas')
    
    return render(request, 'concretar_adopciones_aceptadas.html', {'solicitudes_aceptadas': solicitudes_aceptadas})

@login_required
@administrador_requerido
def crear_administrador(request):
    if request.method == 'POST':
        form = FormularioCrearAdministrador(request.POST, request=request)
        if form.is_valid():
            try:
                usuario = form.save()
                messages.success(request, f'✅ Administrador creado exitosamente.')
                return redirect('adopciones:listar_administradores')
            except Exception as e:
                messages.error(request, f'❌ Error: {str(e)}')
        else:
            messages.error(request, '❌ Corrige los errores del formulario.')
    else:
        form = FormularioCrearAdministrador(request=request)
    
    return render(request, 'crear_administrador.html', {'form': form})

@login_required
@administrador_requerido
def listar_administradores(request):
    administradores = Usuario.objects.filter(rol='administrador').order_by('email')
    administradores_activos = administradores.filter(is_active=True).count()
    administradores_inactivos = administradores.filter(is_active=False).count()
    
    return render(request, 'listar_administradores.html', {
        'administradores': administradores,
        'administradores_activos': administradores_activos,
        'administradores_inactivos': administradores_inactivos,
    })

@login_required
@administrador_requerido
def editar_administrador(request, administrador_id):
    administrador = get_object_or_404(Usuario, id=administrador_id, rol='administrador')
    
    # No permitir que un admin edite a sí mismo en esta vista
    if administrador.id == request.user.id:
        messages.warning(request, 'Para editar tu propio perfil, usa la sección de perfil.')
        return redirect('adopciones:listar_administradores')
    
    if request.method == 'POST':
        form = FormularioEditarAdministrador(request.POST, instance=administrador, request=request)
        if form.is_valid():
            form.save()
            messages.success(request, f'✅ Administrador {administrador.get_nombre_completo()} actualizado exitosamente.')
            return redirect('adopciones:listar_administradores')
        else:
            messages.error(request, '❌ Por favor corrige los errores del formulario.')
    else:
        form = FormularioEditarAdministrador(instance=administrador, request=request)
    
    return render(request, 'editar_administrador.html', {
        'form': form,
        'administrador': administrador
    })

@login_required
@administrador_requerido
def desactivar_administrador(request, administrador_id):
    administrador = get_object_or_404(Usuario, id=administrador_id, rol='administrador')
    
    # No permitir que un admin se desactive a sí mismo
    if administrador.id == request.user.id:
        messages.error(request, '❌ No puedes desactivar tu propia cuenta.')
        return redirect('adopciones:listar_administradores')
    
    if request.method == 'POST':
        form = FormularioCambiarPasswordAdmin(request.POST, request=request)
        if form.is_valid():
            if administrador.is_active:
                administrador.is_active = False
                action_msg = 'desactivado'
                msg_type = 'warning'
            else:
                administrador.is_active = True
                action_msg = 'activado'
                msg_type = 'success'
            
            administrador.save()
            messages.add_message(request, messages.WARNING if not administrador.is_active else messages.SUCCESS, 
                               f'✅ Administrador {administrador.get_nombre_completo()} {action_msg} exitosamente.')
            return redirect('adopciones:listar_administradores')
        else:
            messages.error(request, '❌ Contraseña incorrecta.')
    else:
        form = FormularioCambiarPasswordAdmin(request=request)
    
    return render(request, 'desactivar_administrador.html', {
        'form': form,
        'administrador': administrador
    })