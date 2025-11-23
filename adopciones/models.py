from django.db import models

from django.contrib.auth.models import Usuario
import uuid
from datetime import fecha

class NodoMascota:
    """Nodo para la lista enlazada del árbol binario"""
    def __init__(self, mascota):
        self.mascota = mascota
        self.izquierda = None
        self.derecha = None

class ArbolMascotas:
    """Árbol binario de búsqueda para organizar mascotas"""
    def __init__(self):
        self.raiz = None
    
    def insertar(self, mascota):
        """Insertar una mascota en el árbol"""
        if self.raiz is None:
            self.raiz = NodoMascota(mascota)
        else:
            self._insertar_recursivo(mascota, self.raiz)
    
    def _insertar_recursivo(self, mascota, nodo_actual):
        """Método recursivo para insertar"""
        if mascota.nombre.lower() < nodo_actual.mascota.nombre.lower():
            if nodo_actual.izquierda is None:
                nodo_actual.izquierda = NodoMascota(mascota)
            else:
                self._insertar_recursivo(mascota, nodo_actual.izquierda)
        else:
            if nodo_actual.derecha is None:
                nodo_actual.derecha = NodoMascota(mascota)
            else:
                self._insertar_recursivo(mascota, nodo_actual.derecha)
    
    def obtener_en_orden(self):
        """Obtener mascotas en orden"""
        mascotas = []
        self._en_orden_recursivo(self.raiz, mascotas)
        return mascotas
    
    def _en_orden_recursivo(self, nodo, mascotas):
        """Recorrido en orden recursivo"""
        if nodo is not None:
            self._en_orden_recursivo(nodo.izquierda, mascotas)
            mascotas.append(nodo.mascota)
            self._en_orden_recursivo(nodo.derecha, mascotas)

class NodoSolicitud:
    """Nodo para la lista enlazada de la cola"""
    def __init__(self, solicitud):
        self.solicitud = solicitud
        self.siguiente = None

class ColaSolicitudes:
    """Cola para manejar solicitudes de adopción usando lista enlazada"""
    def __init__(self):
        self.frente = None
        self.final = None
        self.tamaño = 0
    
    def esta_vacia(self):
        """Verificar si la cola está vacía"""
        return self.frente is None
    
    def encolar(self, solicitud):
        """Agregar una solicitud a la cola"""
        nuevo_nodo = NodoSolicitud(solicitud)
        
        if self.final is None:
            self.frente = self.final = nuevo_nodo
        else:
            self.final.siguiente = nuevo_nodo
            self.final = nuevo_nodo
        
        self.tamaño += 1
    
    def desencolar(self):
        """Remover y retornar la solicitud del frente"""
        if self.esta_vacia():
            return None
        
        solicitud = self.frente.solicitud
        self.frente = self.frente.siguiente
        
        if self.frente is None:
            self.final = None
        
        self.tamaño -= 1
        return solicitud
    
    def ver_frente(self):
        """Ver la solicitud del frente sin removerla"""
        if self.esta_vacia():
            return None
        return self.frente.solicitud

class MultiColas:
    """Manejador de múltiples colas (una por mascota)"""
    def __init__(self):
        self.colas_por_mascota = {}
    
    def agregar_solicitud(self, mascota_id, solicitud):
        """Agregar solicitud a la cola de una mascota específica"""
        if mascota_id not in self.colas_por_mascota:
            self.colas_por_mascota[mascota_id] = ColaSolicitudes()
        
        self.colas_por_mascota[mascota_id].encolar(solicitud)
    
    def obtener_siguiente_solicitud(self, mascota_id):
        """Obtener la siguiente solicitud para una mascota"""
        if mascota_id in self.colas_por_mascota:
            return self.colas_por_mascota[mascota_id].desencolar()
        return None
    
    def ver_siguiente_solicitud(self, mascota_id):
        """Ver la siguiente solicitud sin removerla"""
        if mascota_id in self.colas_por_mascota:
            return self.colas_por_mascota[mascota_id].ver_frente()
        return None
    
    def obtener_tamaño_cola(self, mascota_id):
        """Obtener el tamaño de la cola de una mascota"""
        if mascota_id in self.colas_por_mascota:
            return self.colas_por_mascota[mascota_id].tamaño
        return 0

class Mascota(models.Model):
    """Modelo para representar una mascota"""
    
    TIPOS_MASCOTA = [
        ('perro', 'Perro'),
        ('gato', 'Gato'),
    ]
    
    TAMAÑOS = [
        ('pequeño', 'Pequeño'),
        ('mediano', 'Mediano'),
        ('grande', 'Grande'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    tipo_mascota = models.CharField(max_length=20, choices=TIPOS_MASCOTA, verbose_name="Tipo")
    raza = models.CharField(max_length=100, verbose_name="Raza")
    edad = models.IntegerField(verbose_name="Edad (años)")
    tamaño = models.CharField(max_length=20, choices=TAMAÑOS, verbose_name="Tamaño")
    descripcion = models.TextField(verbose_name="Descripción")
    foto = models.ImageField(upload_to='mascotas/', verbose_name="Foto")
    disponible = models.BooleanField(default=True, verbose_name="Disponible para adopción")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_mascota_display()}"

class Adoptante(models.Model):
    """Modelo para representar un adoptante"""
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE)
    telefono = models.CharField(max_length=15, verbose_name="Teléfono")
    direccion = models.TextField(verbose_name="Dirección")
    numero_identificacion = models.CharField(max_length=20, unique=True, verbose_name="Número de Identificación")
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.numero_identificacion}"

class SolicitudAdopcion(models.Model):
    """Modelo para representar una solicitud de adopción"""
    
    ESTADOS = [
        ('espera', 'En espera'),
        ('aceptado', 'Aceptado'),
        ('concretado', 'Concretado'),
        ('rechazado', 'Rechazado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, verbose_name="Mascota")
    adoptante = models.ForeignKey(Adoptante, on_delete=models.CASCADE, verbose_name="Adoptante")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='espera', verbose_name="Estado")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_procesamiento = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True, verbose_name="Notas adicionales")
    
    def __str__(self):
        return f"Solicitud de {self.adoptante} para {self.mascota}"

class CompromisoAdopcion(models.Model):
    """Modelo para representar el compromiso de adopción"""
    solicitud_adopcion = models.OneToOneField(SolicitudAdopcion, on_delete=models.CASCADE)
    fecha_compromiso = models.DateField(default=fecha.today)
    documento_pdf = models.FileField(upload_to='compromisos/')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Compromiso - {self.solicitud_adopcion}"