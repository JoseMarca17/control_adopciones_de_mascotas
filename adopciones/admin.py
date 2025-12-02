from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, PerfilAdoptante, Mascota, SolicitudAdopcion, CompromisoAdopcion

@admin.register(Usuario)
class AdminUsuarioPersonalizado(UserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'rol', 'is_active']
    list_filter = ['rol', 'is_active', 'is_staff', 'fecha_registro']
    search_fields = ['email', 'first_name', 'last_name', 'telefono']
    ordering = ['-fecha_registro']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'telefono', 'direccion', 'fecha_nacimiento')}),
        ('Permisos', {'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'fecha_registro')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'rol'),
        }),
    )
    
    readonly_fields = ['fecha_registro']

@admin.register(PerfilAdoptante)
class AdminPerfilAdoptante(admin.ModelAdmin):
    list_display = ['usuario', 'numero_identificacion', 'tipo_vivienda', 'tiene_patio']
    list_filter = ['tipo_vivienda', 'tiene_patio']
    search_fields = ['usuario__first_name', 'usuario__last_name', 'numero_identificacion']

@admin.register(Mascota)
class AdminMascota(admin.ModelAdmin):
    list_display = ['nombre', 'tipo_mascota', 'raza', 'sexo', 'edad_display', 'disponible', 'fecha_ingreso']
    list_filter = ['tipo_mascota', 'sexo', 'tamaño', 'disponible', 'vacunado', 'esterilizado']
    search_fields = ['nombre', 'raza']
    readonly_fields = ['fecha_creacion']
    
    def edad_display(self, obj):
        return obj.edad_display
    edad_display.short_description = 'Edad'
    edad_display.admin_order_field = 'edad_valor'

@admin.register(SolicitudAdopcion)
class AdminSolicitudAdopcion(admin.ModelAdmin):
    list_display = ['mascota', 'adoptante', 'estado', 'fecha_solicitud']
    list_filter = ['estado', 'fecha_solicitud']
    search_fields = ['mascota__nombre', 'adoptante__first_name']
    readonly_fields = ['fecha_solicitud']

@admin.register(CompromisoAdopcion)
class AdminCompromisoAdopcion(admin.ModelAdmin):
    list_display = ['solicitud_adopcion', 'fecha_compromiso']
    search_fields = ['solicitud_adopcion__mascota__nombre']