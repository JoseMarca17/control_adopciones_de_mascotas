from django import forms
from .models import Mascota, SolicitudAdopcion, PerfilAdoptante, Usuario

class FormularioMascota(forms.ModelForm):
    class Meta:
        model = Mascota
        fields = ['nombre', 'tipo_mascota', 'raza', 'edad', 'tamaño', 'descripcion', 'foto', 
                 'vacunado', 'esterilizado', 'desparasitado', 'observaciones_medicas']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
            'observaciones_medicas': forms.Textarea(attrs={'rows': 3}),
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
    class Meta:
        model = SolicitudAdopcion
        fields = ['notas']
        widgets = {
            'notas': forms.Textarea(attrs={
                'rows': 4, 
                'placeholder': 'Explica por qué quieres adoptar esta mascota y cómo será su nuevo hogar...'
            }),
        }
        labels = {
            'notas': 'Motivos de la adopción',
        }

class FormularioRegistroAdoptante(forms.ModelForm):
    telefono = forms.CharField(max_length=15, label="Teléfono")
    direccion = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label="Dirección")
    numero_identificacion = forms.CharField(max_length=20, label="Número de Identificación")
    ocupacion = forms.CharField(max_length=100, required=False, label="Ocupación")
    experiencia_mascotas = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}), 
        required=False, 
        label="Experiencia con mascotas"
    )
    tipo_vivienda = forms.ChoiceField(
        choices=[
            ('casa', 'Casa'),
            ('apartamento', 'Apartamento'),
            ('finca', 'Finca'),
        ],
        label="Tipo de vivienda"
    )
    tiene_patio = forms.BooleanField(required=False, label="¿Tiene patio?")
    otras_mascotas = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}), 
        required=False, 
        label="Otras mascotas en casa"
    )
    
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name']
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
        }