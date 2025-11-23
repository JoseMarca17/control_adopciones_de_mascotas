from django.contrib import admin
from .models import Mascota, Adoptante, SolicitudAdopcion, CompromisoAdopcion

@admin.register(Mascota)
class AdminMascota(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_mascota', 'raza', 'edad', 'disponible']
    list_filter = ['tipo_mascota', 'tamaño', 'disponible']
    search_fields = ['nombre', 'raza']

@admin.register(Adoptante)
class AdminAdoptante(admin.ModelAdmin):
    list_display = ['usuario', 'telefono', 'numero_identificacion']
    search_fields = ['usuario__first_name', 'usuario__last_name', 'numero_identificacion']

@admin.register(SolicitudAdopcion)
class AdminSolicitudAdopcion(admin.ModelAdmin):
    list_display = ['mascota', 'adoptante', 'estado', 'fecha_solicitud']
    list_filter = ['estado', 'fecha_solicitud']
    search_fields = ['mascota__nombre', 'adoptante__usuario__first_name']

@admin.register(CompromisoAdopcion)
class AdminCompromisoAdopcion(admin.ModelAdmin):
    list_display = ['solicitud_adopcion', 'fecha_compromiso']
    search_fields = ['solicitud_adopcion__mascota__nombre']