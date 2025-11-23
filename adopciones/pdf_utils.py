from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import date
from django.http import HttpResponse

def generar_compromiso_adopcion(solicitud_adopcion):
    
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # Centrado
        textColor=colors.darkblue
    )
    
    estilo_subtitulo = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        spaceAfter=12,
        textColor=colors.darkblue
    )
    
    estilo_normal = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=12
    )

    contenido = []

    contenido.append(Paragraph("COMPROMISO DE ADOPCIÓN", estilo_titulo))
    contenido.append(Paragraph("Asociación 'Adopta un Amigo'", estilo_subtitulo))
    contenido.append(Spacer(1, 20))

    contenido.append(Paragraph(f"<b>Fecha:</b> {date.today().strftime('%d de %B de %Y')}", estilo_normal))
    contenido.append(Spacer(1, 20))

    contenido.append(Paragraph("<b>INFORMACIÓN DEL ADOPTANTE</b>", estilo_subtitulo))
    contenido.append(Paragraph(f"<b>Nombre:</b> {solicitud_adopcion.adoptante.get_nombre_completo()}", estilo_normal))
    contenido.append(Paragraph(f"<b>Email:</b> {solicitud_adopcion.adoptante.email}", estilo_normal))
    contenido.append(Paragraph(f"<b>Teléfono:</b> {solicitud_adopcion.adoptante.telefono}", estilo_normal))
    contenido.append(Paragraph(f"<b>Dirección:</b> {solicitud_adopcion.adoptante.direccion}", estilo_normal))
    
    if hasattr(solicitud_adopcion.adoptante, 'perfil_adoptante'):
        perfil = solicitud_adopcion.adoptante.perfil_adoptante
        contenido.append(Paragraph(f"<b>Identificación:</b> {perfil.numero_identificacion}", estilo_normal))
        contenido.append(Paragraph(f"<b>Ocupación:</b> {perfil.ocupacion}", estilo_normal))
    
    contenido.append(Spacer(1, 20))

    contenido.append(Paragraph("<b>INFORMACIÓN DE LA MASCOTA</b>", estilo_subtitulo))
    contenido.append(Paragraph(f"<b>Nombre:</b> {solicitud_adopcion.mascota.nombre}", estilo_normal))
    contenido.append(Paragraph(f"<b>Tipo:</b> {solicitud_adopcion.mascota.get_tipo_mascota_display()}", estilo_normal))
    contenido.append(Paragraph(f"<b>Raza:</b> {solicitud_adopcion.mascota.raza}", estilo_normal))
    contenido.append(Paragraph(f"<b>Edad:</b> {solicitud_adopcion.mascota.edad} años", estilo_normal))
    contenido.append(Paragraph(f"<b>Tamaño:</b> {solicitud_adopcion.mascota.get_tamaño_display()}", estilo_normal))

    info_medica = []
    if solicitud_adopcion.mascota.vacunado:
        info_medica.append("✓ Vacunado")
    if solicitud_adopcion.mascota.esterilizado:
        info_medica.append("✓ Esterilizado")
    if solicitud_adopcion.mascota.desparasitado:
        info_medica.append("✓ Desparasitado")
    
    if info_medica:
        contenido.append(Paragraph(f"<b>Estado médico:</b> {', '.join(info_medica)}", estilo_normal))
    
    contenido.append(Spacer(1, 20))

    contenido.append(Paragraph("<b>COMPROMISOS DEL ADOPTANTE</b>", estilo_subtitulo))
    
    compromisos = [
        "Proporcionar un hogar amoroso, seguro y permanente",
        "Brindar alimentación adecuada y agua fresca diariamente",
        "Proporcionar atención veterinaria regular y cuando sea necesario",
        "Mantener al día las vacunas y desparasitaciones",
        "Proporcionar ejercicio adecuado y enriquecimiento ambiental",
        "Nunca abandonar, maltratar o descuidar a la mascota",
        "Notificar a la asociación si no puede continuar con el cuidado",
        "Permitir visitas de seguimiento por parte de la asociación",
        "Proporcionar identificación (collar con placa) a la mascota",
        "Mantener a la mascota en un ambiente limpio y saludable"
    ]
    
    for i, compromiso in enumerate(compromisos, 1):
        contenido.append(Paragraph(f"{i}. {compromiso}", estilo_normal))
    
    contenido.append(Spacer(1, 30))

    tabla_firmas = Table([
        ['_________________________', '_________________________'],
        ['Firma del Adoptante', 'Representante de la Asociación'],
        [solicitud_adopcion.adoptante.get_nombre_completo(), 'Asociación "Adopta un Amigo"']
    ], colWidths=[3*inch, 3*inch])
    
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    contenido.append(tabla_firmas)

    doc.build(contenido)

    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf

def generar_reporte_adopciones(datos_reporte):
    buffer = BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    contenido = []

    contenido.append(Paragraph("REPORTE DE ADOPCIONES", styles['Heading1']))
    contenido.append(Paragraph(f"Fecha: {date.today().strftime('%d/%m/%Y')}", styles['Normal']))
    contenido.append(Spacer(1, 20))

    contenido.append(Paragraph("ESTADÍSTICAS GENERALES", styles['Heading2']))
    
    datos_estadisticas = [
        ['Total Mascotas', str(datos_reporte['total_mascotas'])],
        ['Mascotas Disponibles', str(datos_reporte['mascotas_disponibles'])],
        ['Total Adopciones', str(datos_reporte['total_adopciones'])],
        ['Solicitudes Pendientes', str(datos_reporte['solicitudes_pendientes'])],
    ]
    
    tabla_estadisticas = Table(datos_estadisticas, colWidths=[3*inch, 2*inch])
    tabla_estadisticas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    contenido.append(tabla_estadisticas)
    contenido.append(Spacer(1, 20))

    contenido.append(Paragraph("MASCOTAS POR TIPO", styles['Heading2']))
    
    datos_tipos = [
        ['Tipo', 'Cantidad'],
        ['Perros', str(datos_reporte['perros'])],
        ['Gatos', str(datos_reporte['gatos'])],
    ]
    
    tabla_tipos = Table(datos_tipos, colWidths=[3*inch, 2*inch])
    tabla_tipos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    contenido.append(tabla_tipos)

    doc.build(contenido)
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf