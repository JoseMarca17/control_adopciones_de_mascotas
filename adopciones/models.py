from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid
from datetime import date

class ManejadorUsuarioPersonalizado(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields): 
        if not email:
            raise ValueError('El email es obligatorio')
        
        email = self.normalize_email(email)
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password=None, **extra_fields): 
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('rol', 'administrador')
        return self.create_user(email, password, **extra_fields)  # 

class Usuario(AbstractUser):
    ROLES = [
        ('administrador', 'Administrador'),
        ('adoptante', 'Adoptante'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  
    email = models.EmailField('email', unique=True)
    telefono = models.CharField('teléfono', max_length=15, blank=True)
    direccion = models.TextField('dirección', blank=True)
    fecha_nacimiento = models.DateField('fecha de nacimiento', null=True, blank=True)
    rol = models.CharField('rol', max_length=20, choices=ROLES, default='adoptante')
    fecha_registro = models.DateTimeField('fecha de registro', auto_now_add=True)
    
    first_name = models.CharField('nombre', max_length=30, blank=False)
    last_name = models.CharField('apellido', max_length=30, blank=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = ManejadorUsuarioPersonalizado()
    
    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'
    
    def __str__(self):
        return f"{self.get_nombre_completo()} - {self.email}"
    
    def get_nombre_completo(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    @property
    def es_administrador(self):
        return self.rol == 'administrador'
    
    @property
    def es_adoptante(self):
        return self.rol == 'adoptante'

class PerfilAdoptante(models.Model):
    usuario = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE,
        related_name='perfil_adoptante'
    )
    numero_identificacion = models.CharField('número de identificación', max_length=20, unique=True)
    ocupacion = models.CharField('ocupación', max_length=100, blank=True)
    experiencia_mascotas = models.TextField('experiencia con mascotas', blank=True)
    tipo_vivienda = models.CharField(
        'tipo de vivienda',
        max_length=50,
        choices=[
            ('casa', 'Casa'),
            ('departamento', 'Departamento'),
        ],
        default='casa'
    )
    tiene_patio = models.BooleanField('tiene patio', default=False)
    otras_mascotas = models.TextField('otras mascotas en casa', blank=True)
    fecha_creacion = models.DateTimeField('fecha de creación', auto_now_add=True)
    
    class Meta:
        verbose_name = 'perfil de adoptante'
        verbose_name_plural = 'perfiles de adoptantes'
    
    def __str__(self):
        return f"Perfil de {self.usuario.get_nombre_completo()}"

class NodoMascota:
    def __init__(self, mascota):
        self.mascota = mascota
        self.izquierda = None
        self.derecha = None

class ArbolMascotas:
    def __init__(self):
        self.raiz = None
    
    def insertar(self, mascota):
        if self.raiz is None:
            self.raiz = NodoMascota(mascota)
        else:
            self._insertar_recursivo(mascota, self.raiz)
    
    def _insertar_recursivo(self, mascota, nodo_actual):
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
        mascotas = []
        self._en_orden_recursivo(self.raiz, mascotas)
        return mascotas
    
    def eliminar(self, mascota):
        self.raiz = self._eliminar_recursivo(mascota, self.raiz)
    
    def _eliminar_recursivo(self, mascota, nodo_actual):
        if nodo_actual is None:
            return None
            
        if mascota.nombre.lower() < nodo_actual.mascota.nombre.lower():
            nodo_actual.izquierda = self._eliminar_recursivo(mascota, nodo_actual.izquierda)
        elif mascota.nombre.lower() > nodo_actual.mascota.nombre.lower():
            nodo_actual.derecha = self._eliminar_recursivo(mascota, nodo_actual.derecha)
        else:
            if nodo_actual.izquierda is None:
                return nodo_actual.derecha
            elif nodo_actual.derecha is None:
                return nodo_actual.izquierda
            else:
                sucesor = self._encontrar_minimo(nodo_actual.derecha)
                nodo_actual.mascota = sucesor.mascota
                nodo_actual.derecha = self._eliminar_recursivo(sucesor.mascota, nodo_actual.derecha)
        
        return nodo_actual
    
    def _encontrar_minimo(self, nodo):
        actual = nodo
        while actual.izquierda is not None:
            actual = actual.izquierda
        return actual
    
    def _en_orden_recursivo(self, nodo, mascotas):
        if nodo is not None:
            self._en_orden_recursivo(nodo.izquierda, mascotas)
            mascotas.append(nodo.mascota)
            self._en_orden_recursivo(nodo.derecha, mascotas)

class NodoSolicitud:
    def __init__(self, solicitud):
        self.solicitud = solicitud
        self.siguiente = None

class ColaSolicitudes:
    def __init__(self):
        self.frente = None
        self.final = None
        self.tamaño = 0
    
    def esta_vacia(self):
        return self.frente is None
    
    def encolar(self, solicitud):
        nuevo_nodo = NodoSolicitud(solicitud)
        
        if self.final is None:
            self.frente = self.final = nuevo_nodo
        else:
            self.final.siguiente = nuevo_nodo
            self.final = nuevo_nodo
        
        self.tamaño += 1
    
    def desencolar(self):
        if self.esta_vacia():
            return None
        
        solicitud = self.frente.solicitud
        self.frente = self.frente.siguiente
        
        if self.frente is None:
            self.final = None
        
        self.tamaño -= 1
        return solicitud
    
    def ver_frente(self):
        if self.esta_vacia():
            return None
        return self.frente.solicitud

class MultiColas:
    def __init__(self):
        self.colas_por_mascota = {}
    
    def agregar_solicitud(self, mascota_id, solicitud):
        if mascota_id not in self.colas_por_mascota:
            self.colas_por_mascota[mascota_id] = ColaSolicitudes()
        
        self.colas_por_mascota[mascota_id].encolar(solicitud)
    
    def obtener_siguiente_solicitud(self, mascota_id):
        if mascota_id in self.colas_por_mascota:
            return self.colas_por_mascota[mascota_id].desencolar()
        return None
    
    def ver_siguiente_solicitud(self, mascota_id):
        if mascota_id in self.colas_por_mascota:
            return self.colas_por_mascota[mascota_id].ver_frente()
        return None
    
    def obtener_tamaño_cola(self, mascota_id):
        if mascota_id in self.colas_por_mascota:
            return self.colas_por_mascota[mascota_id].tamaño
        return 0

class Mascota(models.Model):
    
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
    nombre = models.CharField('nombre', max_length=100)
    tipo_mascota = models.CharField('tipo', max_length=20, choices=TIPOS_MASCOTA)
    raza = models.CharField('raza', max_length=100)
    edad = models.IntegerField('edad (años)')
    tamaño = models.CharField('tamaño', max_length=20, choices=TAMAÑOS)
    descripcion = models.TextField('descripción')
    foto = models.ImageField('foto', upload_to='mascotas/')
    disponible = models.BooleanField('disponible para adopción', default=True)
    fecha_ingreso = models.DateField('fecha de ingreso', default=date.today)
    fecha_creacion = models.DateTimeField('fecha de creación', auto_now_add=True)
    vacunado = models.BooleanField('vacunado', default=False)
    esterilizado = models.BooleanField('esterilizado', default=False)
    desparasitado = models.BooleanField('desparasitado', default=False)
    observaciones_medicas = models.TextField('observaciones médicas', blank=True)
    
    class Meta:
        verbose_name = 'mascota'
        verbose_name_plural = 'mascotas'
        ordering = ['-fecha_creacion']
        
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_mascota_display()}"
    
    def puede_ser_editada(self):
        return not self.solicitudadopcion_set.filter(estado__in=['aceptado', 'concretado']).exists()
    
    def puede_ser_eliminada(self):
        return not self.solicitudadopcion_set.exists()
    
    def __str__(self):
        return f"{self.nombre} - {self.get_tipo_mascota_display()}"

class SolicitudAdopcion(models.Model):
    
    ESTADOS = [
        ('espera', 'En espera'),
        ('aceptado', 'Aceptado'),
        ('rechazado', 'Rechazado'),
        ('concretado', 'Concretado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, verbose_name="mascota")
    adoptante = models.ForeignKey(Usuario, on_delete=models.CASCADE, verbose_name="adoptante")
    estado = models.CharField('estado', max_length=20, choices=ESTADOS, default='espera')
    fecha_solicitud = models.DateTimeField('fecha de solicitud', auto_now_add=True)
    fecha_procesamiento = models.DateTimeField('fecha de procesamiento', null=True, blank=True)
    notas = models.TextField('notas adicionales', blank=True)
    
    class Meta:
        verbose_name = 'solicitud de adopción'
        verbose_name_plural = 'solicitudes de adopción'
        ordering = ['-fecha_solicitud']
    
    def __str__(self):
        return f"Solicitud de {self.adoptante.get_nombre_completo()} para {self.mascota.nombre}"

class CompromisoAdopcion(models.Model):
    
    solicitud_adopcion = models.OneToOneField(SolicitudAdopcion, on_delete=models.CASCADE)
    fecha_compromiso = models.DateField('fecha de compromiso', default=date.today)
    documento_pdf = models.FileField('documento PDF', upload_to='compromisos/')
    fecha_creacion = models.DateTimeField('fecha de creación', auto_now_add=True)
    
    class Meta:
        verbose_name = 'compromiso de adopción'
        verbose_name_plural = 'compromisos de adopción'
    
    def __str__(self):
        return f"Compromiso - {self.solicitud_adopcion}"