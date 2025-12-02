from django import forms
from .models import Mascota, SolicitudAdopcion, PerfilAdoptante, Usuario
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

class FormularioMascota(forms.ModelForm):
    class Meta:
        model = Mascota
        fields = [
            'nombre', 'tipo_mascota', 'raza', 'sexo', 'edad_valor', 'edad_unidad',
            'tamaño', 'descripcion', 'foto', 'disponible', 'vacunado',
            'esterilizado', 'desparasitado', 'observaciones_medicas'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Luna, Max, Toby'
            }),
            'tipo_mascota': forms.Select(attrs={
                'class': 'form-control'
            }),
            'raza': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Labrador, Siames, Mestizo'
            }),
            'sexo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'edad_valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Ej: 6'
            }),
            'edad_unidad': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tamaño': forms.Select(attrs={
                'class': 'form-control'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe su personalidad, comportamiento, etc.'
            }),
            'observaciones_medicas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Alergias, tratamientos especiales, etc.'
            }),
            'disponible': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'vacunado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'esterilizado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'desparasitado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'edad_valor': 'Edad',
            'edad_unidad': 'Unidad de Edad',
            'descripcion': 'Descripción',
            'observaciones_medicas': 'Observaciones Médicas',
        }

class FormularioRegistroUsuario(UserCreationForm):
    email = forms.EmailField(
        label='Correo Electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        label='Nombre',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Apellido',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = ['email', 'first_name', 'last_name', 'password1', 'password2']

class FormularioRegistroAdoptante(forms.ModelForm):
    first_name = forms.CharField(
        label='Nombre',
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Apellido', 
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    telefono = forms.CharField(
        label='Teléfono',
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    direccion = forms.CharField(
        label='Dirección',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True
    )
    
    class Meta:
        model = PerfilAdoptante
        fields = [
            'first_name', 'last_name', 'telefono', 'direccion',
            'numero_identificacion', 'ocupacion', 'experiencia_mascotas',
            'tipo_vivienda', 'tiene_patio', 'otras_mascotas'
        ]
        widgets = {
            'numero_identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'ocupacion': forms.TextInput(attrs={'class': 'form-control'}),
            'experiencia_mascotas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo_vivienda': forms.Select(attrs={'class': 'form-control'}),
            'tiene_patio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'otras_mascotas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class FormularioSolicitudAdopcion(forms.ModelForm):
    class Meta:
        model = SolicitudAdopcion
        fields = ['notas']
        widgets = {
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Cuéntanos por qué quieres adoptar esta mascota, cómo sería su vida contigo, etc.'
            }),
        }
        labels = {
            'notas': 'Motivos para la adopción',
        }

# ✅ FORMA CORRECTA: Usar ModelForm en lugar de UserCreationForm
class FormularioCrearAdministrador(forms.ModelForm):
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña para el nuevo administrador'
        }),
        validators=[validate_password],
        required=True,
        help_text="Mínimo 8 caracteres, no puede ser solo números."
    )
    
    password2 = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite la contraseña'
        }),
        required=True
    )
    
    admin_password = forms.CharField(
        label='Tu Contraseña Actual',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña de administrador'
        }),
        required=True,
        help_text="Debes verificar que eres administrador."
    )
    
    class Meta:
        model = Usuario
        fields = ['email', 'first_name', 'last_name', 'telefono']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono (opcional)'
            }),
        }
        labels = {
            'email': 'Correo Electrónico',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'telefono': 'Teléfono',
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este correo ya está registrado.')
        return email
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas no coinciden.')
        
        return password2
    
    def clean_admin_password(self):
        admin_password = self.cleaned_data.get('admin_password')
        
        if not self.request or not self.request.user.is_authenticated:
            raise ValidationError("Debes estar autenticado.")
        
        if not self.request.user.check_password(admin_password):
            raise ValidationError("Contraseña de administrador incorrecta.")
        
        # Verificar que el usuario actual sea administrador
        if not self.request.user.es_administrador:
            raise ValidationError("Solo los administradores pueden crear otros administradores.")
        
        return admin_password
    
    def save(self, commit=True):
        # Crear usuario pero no guardar aún
        usuario = super().save(commit=False)
        
        # Establecer contraseña
        usuario.set_password(self.cleaned_data['password1'])
        
        # Forzar rol de administrador
        usuario.rol = 'administrador'
        usuario.is_staff = True
        usuario.is_active = True
        
        if commit:
            usuario.save()
        
        return usuario

# OPCIÓN ALTERNATIVA: Si prefieres separar la verificación en un formulario aparte
class FormularioVerificacionAdministrador(forms.Form):
    admin_password = forms.CharField(
        label='Contraseña de Administrador',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña actual'
        }),
        required=True,
        help_text="Debes verificar tu identidad para crear un nuevo administrador."
    )
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
    def clean_admin_password(self):
        admin_password = self.cleaned_data.get('admin_password')
        
        if not self.request or not self.request.user.is_authenticated:
            raise ValidationError("Debes estar autenticado.")
        
        if not self.request.user.check_password(admin_password):
            raise ValidationError("Contraseña incorrecta.")
        
        if not self.request.user.es_administrador:
            raise ValidationError("Solo los administradores pueden realizar esta acción.")
        
        return admin_password

# forms.py - Agrega estos formularios después de los que ya tienes

class FormularioEditarAdministrador(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['email', 'first_name', 'last_name', 'telefono', 'is_active']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellido'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Teléfono'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_active': 'Usuario activo',
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # No permitir cambiar el email si ya está en uso por otro usuario
        if self.instance.pk:
            self.fields['email'].required = False
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if self.instance.pk:
            # Si el email no cambió, está bien
            if email == self.instance.email:
                return email
        # Verificar si el email ya existe
        if Usuario.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Este correo ya está registrado.')
        return email

class FormularioCambiarPasswordAdmin(forms.Form):
    admin_password = forms.CharField(
        label='Tu Contraseña Actual',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña de administrador'
        }),
        required=True,
        help_text="Debes verificar tu identidad para realizar esta acción."
    )
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
    def clean_admin_password(self):
        admin_password = self.cleaned_data.get('admin_password')
        
        if not self.request or not self.request.user.is_authenticated:
            raise ValidationError("Debes estar autenticado.")
        
        if not self.request.user.check_password(admin_password):
            raise ValidationError("Contraseña de administrador incorrecta.")
        
        return admin_password