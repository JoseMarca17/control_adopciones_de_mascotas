from .models import ArbolMascotas, MultiColas, SolicitudAdopcion

# Instancias globales de las estructuras de datos
arbol_mascotas = ArbolMascotas()
multi_colas = MultiColas()

def inicializar_estructuras():
    """Inicializar las estructuras de datos con información de la base de datos"""
    global arbol_mascotas, multi_colas
    
    # Inicializar árbol con mascotas disponibles
    from .models import Mascota
    mascotas = Mascota.objects.filter(disponible=True)
    
    for mascota in mascotas:
        arbol_mascotas.insertar(mascota)
    
    # Inicializar multicolas con solicitudes pendientes
    solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado='espera')
    
    for solicitud in solicitudes_pendientes:
        multi_colas.agregar_solicitud(solicitud.mascota.id, solicitud)

def obtener_mascotas_ordenadas():
    """Obtener mascotas ordenadas usando el árbol"""
    return arbol_mascotas.obtener_en_orden()

def agregar_solicitud_cola(mascota_id, solicitud):
    """Agregar una solicitud a la cola de la mascota"""
    multi_colas.agregar_solicitud(mascota_id, solicitud)

def procesar_siguiente_solicitud(mascota_id):
    """Procesar la siguiente solicitud de una mascota"""
    return multi_colas.obtener_siguiente_solicitud(mascota_id)

def ver_siguiente_solicitud(mascota_id):
    """Ver la siguiente solicitud sin procesarla"""
    return multi_colas.ver_siguiente_solicitud(mascota_id)

def obtener_cantidad_solicitudes(mascota_id):
    """Obtener la cantidad de solicitudes en cola para una mascota"""
    return multi_colas.obtener_tamaño_cola(mascota_id)