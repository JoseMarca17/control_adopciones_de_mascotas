from django.urls import path
from . import views

app_name = 'adopciones'

urlpatterns = [
    path('', views.index, name='index'), 
    path('catalogo/', views.catalog, name='catalog'),
    path('mascota/<uuid:mascota_id>/', views.detalles_mascota, name='detalles_mascota'),
    path('solicitar-adopcion/<uuid:mascota_id>/', views.solicitud_adopcion, name='solicitud_adopcion'),
    path('registrar-adoptante/', views.registrar_adoptante, name='registrar_adoptante'),
    path('admin/panel/', views.dashboard, name='dashboard'),
    path('admin/agregar-mascota/', views.agregar_mascota, name='agregar_mascota'),
    path('admin/procesar-solicitudes/', views.procesar_solicitud, name='procesar_solicitud'),
    path('admin/procesar-solicitudes/<uuid:mascota_id>/', views.procesar_solicitud_mascota, name='procesar_solicitud_mascota'),
    path('admin/generar-compromiso/<uuid:solicitud_id>/', views.generate_commitment, name='generate_commitment'),
    path('admin/reportes/', views.reports, name='reports'),
    path('admin/descargar-reporte-pdf/', views.download_report_pdf, name='download_report_pdf'),
    path('admin/mascotas/', views.listar_mascotas, name='listar_mascotas'),
    path('admin/editar-mascota/<uuid:mascota_id>/', views.editar_mascota, name='editar_mascota'),
    path('admin/eliminar-mascota/<uuid:mascota_id>/', views.eliminar_mascota, name='eliminar_mascota'),
]