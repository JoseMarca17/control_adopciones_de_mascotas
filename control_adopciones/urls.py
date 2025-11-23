"""
URL configuration for control_adopciones project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
"""
URLs principales del proyecto.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as views_auth

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('adopciones.urls')),
    path('iniciar-sesion/', views_auth.LoginView.as_view(template_name='registracion/iniciar_sesion.html'), name='iniciar_sesion'),
    path('cerrar-sesion/', views_auth.LogoutView.as_view(), name='cerrar_sesion'),
] + static(settings.URL_MULTIMEDIA, document_root=settings.DIRECTORIO_MULTIMEDIA)