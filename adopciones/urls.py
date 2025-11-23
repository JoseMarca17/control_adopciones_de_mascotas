"""
URLs para la aplicación de adopciones.
"""

from django.urls import path
from . import views

app_name = 'adopciones'

urlpatterns = [
    path('', views.pagina_inicio, name='inicio'),
    path('catalogo/', views.catalogo, name='catalogo'),
    path('mascota/<uuid:mascota_id>/', views.detalle_mascota, name='detalle_mascota'),
    path('solicitar-adopcion/<uuid:mascota_id>/', views.solicitar_adopcion, name='solicitar_adopcion'),
    path('registrar-adoptante/', views.registrar_adoptante, name='registrar_adoptante'),
    path('admin/panel/', views.panel_administracion, name='panel_administracion'),
    path('admin/agregar-mascota/', views.agregar_mascota, name='agregar_mascota'),
    path('admin/procesar-solicitudes/', views.procesar_solicitudes, name='procesar_solicitudes'),
    path('admin/procesar-solicitudes/<uuid:mascota_id>/', views.procesar_solicitud_mascota, name='procesar_solicitud_mascota'),
    path('admin/generar-compromiso/<uuid:solicitud_id>/', views.generar_compromiso, name='generar_compromiso'),
    path('admin/reportes/', views.reportes, name='reportes'),
]