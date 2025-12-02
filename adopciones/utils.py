from .models import ArbolMascotas, MultiColas

arbol_mascotas = ArbolMascotas()
multi_colas = MultiColas()
estructuras_inicializadas = False

def inicializar_estructuras():
    global arbol_mascotas, multi_colas, estructuras_inicializadas
    
    if estructuras_inicializadas:
        return
        
    try:
        from django.db import connection
        from .models import Mascota, SolicitudAdopcion
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES LIKE 'adopciones_mascota'")
            tabla_mascotas_existe = cursor.fetchone() is not None
            
            cursor.execute("SHOW TABLES LIKE 'adopciones_solicitudadopcion'")
            tabla_solicitudes_existe = cursor.fetchone() is not None
        
        if tabla_mascotas_existe:
            mascotas = Mascota.objects.filter(disponible=True)
            
            for mascota in mascotas:
                arbol_mascotas.insertar(mascota)
        
        if tabla_solicitudes_existe:
            solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado='espera')
            
            for solicitud in solicitudes_pendientes:
                multi_colas.agregar_solicitud(solicitud.mascota.id, solicitud)
        
        estructuras_inicializadas = True
        print("✅ Estructuras de datos inicializadas correctamente")
                
    except Exception as e:
        print(f"⚠️ Advertencia: No se pudieron inicializar las estructuras: {e}")

def obtener_mascotas_ordenadas():
    try:
        if not estructuras_inicializadas:
            inicializar_estructuras()
        return arbol_mascotas.obtener_en_orden()
    except Exception as e:
        print(f"⚠️ Error obteniendo mascotas ordenadas: {e}")
        from .models import Mascota
        return Mascota.objects.filter(disponible=True)

def agregar_solicitud_cola(mascota_id, solicitud):
    try:
        if not estructuras_inicializadas:
            inicializar_estructuras()
        multi_colas.agregar_solicitud(mascota_id, solicitud)
    except Exception as e:
        print(f"⚠️ Error agregando a cola: {e}")

def procesar_siguiente_solicitud(mascota_id):
    try:
        if not estructuras_inicializadas:
            inicializar_estructuras()
        return multi_colas.obtener_siguiente_solicitud(mascota_id)
    except Exception as e:
        print(f"⚠️ Error procesando solicitud: {e}")
        return None

def ver_siguiente_solicitud(mascota_id):
    try:
        if not estructuras_inicializadas:
            inicializar_estructuras()
        return multi_colas.ver_siguiente_solicitud(mascota_id)
    except Exception as e:
        print(f"⚠️ Error viendo solicitud: {e}")
        return None

def obtener_cantidad_solicitudes(mascota_id):
    try:
        if not estructuras_inicializadas:
            inicializar_estructuras()
        return multi_colas.obtener_tamaño_cola(mascota_id)
    except Exception as e:
        print(f"⚠️ Error obteniendo cantidad de solicitudes: {e}")
        from .models import SolicitudAdopcion
        return SolicitudAdopcion.objects.filter(mascota_id=mascota_id, estado='espera').count()

def usuario_es_administrador(usuario):
    return usuario.is_authenticated and hasattr(usuario, 'es_administrador') and usuario.es_administrador

def usuario_es_adoptante(usuario):
    if not usuario.is_authenticated:
        return False
    return usuario.rol == 'adoptante'

def usuario_tiene_perfil_adoptante(usuario):
    if not usuario.is_authenticated:
        return False
    
    if hasattr(usuario, 'perfil_adoptante'):
        try:
            _ = usuario.perfil_adoptante
            return True
        except:
            return False
    return False
