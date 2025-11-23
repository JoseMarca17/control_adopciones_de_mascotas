"""
Formularios para la aplicación de adopciones.
"""

from django import forms
from .models import Mascota, SolicitudAdopcion, Adoptante
from django.contrib.auth.models import User

class FormularioMascota(forms.ModelForm):
    """Formulario para agregar/editar mascotas"""
    class Meta:
        model = Mascota
        fields = ['nombre', 'tipo_mascota', 'raza', 'edad', 'tamaño', 'descripcion', 'foto']
        widgets = {
            'descripcion': forms.Textarea(attrs={'filas': 4}),
        }
        labels = {
            'nombre': 'Nombre de la mascota',
            'tipo_mascota': 'Tipo de mascota',
            'raza': 'Raza',
            'edad': 'Edad (años)',
            'tamaño': 'Tamaño',
            'descripcion': 'Descripción',
            'foto': 'Foto de la mascota',
        }

class FormularioSolicitudAdopcion(forms.ModelForm):
    """Formulario para solicitud de adopción"""
    class Meta:
        model = SolicitudAdopcion
        fields = ['notas']
        widgets = {
            'notas': forms.Textarea(attrs={
                'filas': 4, 
                'placeholder': 'Explica por qué quieres adoptar esta mascota y cómo será su nuevo hogar...'
            }),
        }
        labels = {
            'notas': 'Motivos de la adopción',
        }

class FormularioRegistroAdoptante(forms.ModelForm):
    """Formulario para registro de adoptante"""
    telefono = forms.CharField(max_length=15, label="Teléfono")
    direccion = forms.CharField(widget=forms.Textarea(attrs={'filas': 3}), label="Dirección")
    numero_identificacion = forms.CharField(max_length=20, label="Número de Identificación")
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
        }