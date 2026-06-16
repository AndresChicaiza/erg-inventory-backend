"""
Generador de PDF para facturas electrónicas.
Estructura según estándar DIAN Colombia.
Suministros Dacar S.A.S. — VOLCANO ASADORES
"""
import os
import io
from decimal import Decimal

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT


# ── Colores corporativos ──────────────────────────────────────────────────────
ROJO_VOLCANO = HexColor('#8B1A1A')
GRIS_OSCURO  = HexColor('#2D2D2D')
GRIS_MEDIO   = HexColor('#666666')
GRIS_CLARO   = HexColor('#F5F5F5')
NEGRO        = HexColor('#000000')
BLANCO       = white


def _fmt(valor):
    """Formatea un número como moneda colombiana."""
    try:
        v = Decimal(str(valor))
        return f'$ {v:,.0f}'.replace(',', '.')
    except Exception:
        return f'$ {valor}'


def _pct(valor):
    try:
        return f'{Decimal(str(valor)):.2f}%'
    except Exception:
        return f'{valor}%'


def generar_pdf_factura(factura):
    """
    Genera el PDF de una factura y retorna los bytes.
    Compatible con Django HttpResponse.
    """
    from configuracion.models import ConfiguracionEmpresa
    config  = ConfiguracionEmpresa.objects.first()
    cliente = factura.cliente

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=10*mm,  bottomMargin=15*mm,
    )

    W = A4[0] - 30*mm  # Ancho disponible
    styles = getSampleStyleSheet()

    def style(name, **kwargs):
        s = ParagraphStyle(name, parent=styles['Normal'], **kwargs)
        return s

    s_titulo   = style('titulo',   fontSize=8,  textColor=GRIS_OSCURO, leading=10)
    s_bold     = style('bold',     fontSize=8,  textColor=GRIS_OSCURO, fontName='Helvetica-Bold', leading=10)
    s_small    = style('small',    fontSize=7,  textColor=GRIS_MEDIO,  leading=9)
    s_center   = style('center',   fontSize=8,  textColor=GRIS_OSCURO, alignment=TA_CENTER, leading=10)
    s_right    = style('right',    fontSize=8,  textColor=GRIS_OSCURO, alignment=TA_RIGHT,  leading=10)
    s_bold_r   = style('boldr',    fontSize=8,  textColor=GRIS_OSCURO, fontName='Helvetica-Bold', alignment=TA_RIGHT, leading=10)
    s_red_bold = style('redb',     fontSize=9,  textColor=ROJO_VOLCANO, fontName='Helvetica-Bold', leading=11)
    s_total    = style('total',    fontSize=10, textColor=NEGRO, fontName='Helvetica-Bold', alignment=TA_RIGHT, leading=12)

    elements = []

    # ── ENCABEZADO ────────────────────────────────────────────────────────────
    # Logo (si existe) + datos empresa + número factura

    logo_path = None
    if config and config.logo:
        logo_path = config.logo.path

    # Empresa info
    empresa_lines = []
    nombre_com = config.nombre_comercial if config else 'VOLCANO ASADORES'
    razon      = config.razon_social     if config else 'SUMINISTROS DACAR S.A.S.'
    nit        = f'{config.nit}-{config.digito_verificacion}' if config else '901.334.172-0'
    direccion  = config.direccion        if config else 'CR 17 G # 25 – 78'
    ciudad     = f'{config.ciudad}, {config.departamento}' if config else 'Cali, Valle del Cauca'
    telefono   = config.telefono         if config else '316 691 4910'
    email_emp  = config.email            if config else 'suministrosdacar@gmail.com'
    regimen    = config.regimen          if config else 'Responsable de IVA'

    # Número de factura
    resol_num  = config.resolucion_numero if config and config.resolucion_numero else 'Pendiente resolución DIAN'
    prefijo    = factura.prefijo
    numero     = factura.numero_completo

    # Tabla encabezado: [logo+empresa] [datos factura]
    if logo_path and os.path.exists(logo_path):
        logo_img = Image(logo_path, width=45*mm, height=18*mm, kind='proportional')
        logo_cell = logo_img
    else:
        logo_cell = Paragraph(f'<b>{nombre_com}</b>', style('logotxt', fontSize=14,
                              textColor=ROJO_VOLCANO, fontName='Helvetica-Bold', leading=16))

    empresa_col = [
        logo_cell,
        Spacer(1, 2*mm),
        Paragraph(razon,    s_bold),
        Paragraph(f'NIT: {nit}', s_titulo),
        Paragraph(direccion, s_titulo),
        Paragraph(ciudad,    s_titulo),
        Paragraph(f'Tel: {telefono}', s_titulo),
        Paragraph(email_emp, s_small),
        Paragraph(regimen,   s_small),
    ]

    factura_col = [
        Paragraph(f'<b>FACTURA DE VENTA</b>', style('fv', fontSize=12,
                  textColor=ROJO_VOLCANO, fontName='Helvetica-Bold',
                  alignment=TA_CENTER, leading=14)),
        Spacer(1, 2*mm),
        Paragraph(f'<b>No. {numero}</b>', style('nf', fontSize=11,
                  fontName='Helvetica-Bold', alignment=TA_CENTER, leading=13)),
        Spacer(1, 2*mm),
        Paragraph(f'Fecha emisión: {factura.fecha_emision.strftime("%d/%m/%Y")}', s_center),
        Paragraph(f'Vence: {factura.fecha_vencimiento.strftime("%d/%m/%Y") if factura.fecha_vencimiento else "—"}', s_center),
        Spacer(1, 2*mm),
        Paragraph(f'Resolución DIAN:', s_small),
        Paragraph(resol_num, style('resol', fontSize=7, textColor=GRIS_MEDIO,
                  alignment=TA_CENTER, leading=9)),
    ]

    header_table = Table(
        [[empresa_col, factura_col]],
        colWidths=[W * 0.58, W * 0.42],
    )
    header_table.setStyle(TableStyle([
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW',  (0, 0), (-1, -1), 0.5, ROJO_VOLCANO),
        ('RIGHTPADDING', (0, 0), (0, -1), 8),
        ('LEFTPADDING',  (1, 0), (1, -1), 8),
        ('BACKGROUND', (1, 0), (1, -1), GRIS_CLARO),
        ('BOX',        (1, 0), (1, -1), 0.5, ROJO_VOLCANO),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4*mm))

    # ── DATOS DEL CLIENTE ─────────────────────────────────────────────────────
    dv = f'-{cliente.digito_verificacion}' if cliente.digito_verificacion else ''
    regimen_labels = {
        'RESPONSABLE_IVA':    'Responsable de IVA',
        'NO_RESPONSABLE':     'No Responsable de IVA',
        'REGIMEN_SIMPLE':     'Régimen Simple',
        'GRAN_CONTRIBUYENTE': 'Gran Contribuyente',
        'ESPECIAL':           'Entidad sin ánimo de lucro',
        'PERSONA_NATURAL':    'Persona Natural',
    }
    regimen_cliente = regimen_labels.get(cliente.regimen_tributario, cliente.regimen_tributario)

    cliente_data = [
        [Paragraph('<b>DATOS DEL CLIENTE</b>', style('ch', fontSize=8,
                   fontName='Helvetica-Bold', textColor=BLANCO)),
         '', '', ''],
        ['Razón Social:', Paragraph(f'<b>{cliente.razon_social}</b>', s_bold),
         'Tipo Doc:', Paragraph(f'<b>{cliente.tipo_documento}</b>', s_bold)],
        ['Documento:', Paragraph(f'<b>{cliente.numero_documento}{dv}</b>', s_bold),
         'Régimen:', Paragraph(regimen_cliente, s_titulo)],
        ['Dirección:', Paragraph(cliente.direccion or '—', s_titulo),
         'Ciudad:', Paragraph(f'{cliente.ciudad or "—"}, {cliente.departamento or ""}', s_titulo)],
        ['Teléfono:', Paragraph(cliente.telefono or '—', s_titulo),
         'Email:', Paragraph(cliente.email or '—', s_titulo)],
    ]

    cliente_table = Table(
        cliente_data,
        colWidths=[W*0.15, W*0.35, W*0.15, W*0.35],
    )
    cliente_table.setStyle(TableStyle([
        ('SPAN',        (0, 0), (3, 0)),
        ('BACKGROUND',  (0, 0), (3, 0), ROJO_VOLCANO),
        ('TEXTCOLOR',   (0, 0), (3, 0), BLANCO),
        ('FONTNAME',    (0, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (3, 0), 8),
        ('TOPPADDING',  (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('GRID',        (0, 1), (-1, -1), 0.3, HexColor('#CCCCCC')),
        ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(cliente_table)
    elements.append(Spacer(1, 4*mm))

    # ── CONDICIONES DE PAGO ───────────────────────────────────────────────────
    cond_labels = {
        'Contado': 'Contado', '15_dias': 'Crédito 15 días',
        '30_dias': 'Crédito 30 días', '60_dias': 'Crédito 60 días',
        '90_dias': 'Crédito 90 días',
    }
    condicion  = cond_labels.get(factura.condicion_pago, factura.condicion_pago)
    medio      = factura.get_medio_pago_display()

    cond_data = [[
        Paragraph(f'Condición de pago: <b>{condicion}</b>', s_titulo),
        Paragraph(f'Medio de pago: <b>{medio}</b>', s_titulo),
        Paragraph(f'Estado: <b>{factura.estado}</b>', s_titulo),
    ]]
    cond_table = Table(cond_data, colWidths=[W/3, W/3, W/3])
    cond_table.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), GRIS_CLARO),
        ('TOPPADDING',   (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
        ('LEFTPADDING',  (0, 0), (-1, -1), 6),
        ('BOX',          (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
    ]))
    elements.append(cond_table)
    elements.append(Spacer(1, 4*mm))

    # ── TABLA DE PRODUCTOS ────────────────────────────────────────────────────
    items_header = [
        Paragraph('#', s_bold),
        Paragraph('Descripción', s_bold),
        Paragraph('Cant.', s_bold),
        Paragraph('Precio Unit.', style('ph', fontSize=8, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        Paragraph('Desc.', style('ph', fontSize=8, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        Paragraph('IVA', style('ph', fontSize=8, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph('Subtotal', style('ph', fontSize=8, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        Paragraph('Total', style('ph', fontSize=8, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
    ]

    items_data = [items_header]
    for i, det in enumerate(factura.detalles.all().order_by('orden', 'id'), start=1):
        desc = det.descripcion
        if det.es_obsequio:
            desc += ' <font color="#8B1A1A"><b>(OBSEQUIO)</b></font>'

        items_data.append([
            Paragraph(str(i), s_center),
            Paragraph(desc, s_titulo),
            Paragraph(f'{det.cantidad:g}', s_center),
            Paragraph(_fmt(det.precio_unitario), s_right),
            Paragraph(f'{det.descuento_pct:g}%' if not det.es_obsequio else '100%', s_right),
            Paragraph(f'{det.iva_tipo}%' if det.iva_tipo not in ('EXCLUIDO',) else 'EXC', s_center),
            Paragraph(_fmt(det.subtotal_linea), s_right),
            Paragraph(_fmt(det.total_linea), s_right),
        ])

    items_table = Table(
        items_data,
        colWidths=[
            W*0.04, W*0.30, W*0.07,
            W*0.12, W*0.07, W*0.07,
            W*0.14, W*0.14,
        ],
        repeatRows=1,
    )
    items_table.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), GRIS_OSCURO),
        ('TEXTCOLOR',     (0, 0), (-1, 0), BLANCO),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 3),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [BLANCO, GRIS_CLARO]),
        ('GRID',          (0, 0), (-1, -1), 0.3, HexColor('#CCCCCC')),
        ('LINEBELOW',     (0, 0), (-1, 0), 1, ROJO_VOLCANO),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 4*mm))

    # ── RESUMEN DE TOTALES ────────────────────────────────────────────────────
    def fila_total(label, valor, bold=False, color=NEGRO):
        ls = s_right if not bold else s_bold_r
        return [
            Paragraph(label, style('tl', fontSize=8, textColor=color,
                      fontName='Helvetica-Bold' if bold else 'Helvetica',
                      alignment=TA_RIGHT)),
            Paragraph(valor, style('tv', fontSize=8, textColor=color,
                      fontName='Helvetica-Bold' if bold else 'Helvetica',
                      alignment=TA_RIGHT)),
        ]

    totales_data = [
        fila_total('Subtotal:', _fmt(factura.subtotal)),
    ]

    if factura.descuento_total > 0:
        totales_data.append(fila_total('(-) Descuentos:', _fmt(factura.descuento_total)))

    if factura.base_iva_19 > 0:
        totales_data.append(fila_total(f'Base IVA 19%:', _fmt(factura.base_iva_19)))
        totales_data.append(fila_total(f'IVA 19%:', _fmt(factura.valor_iva_19)))

    if factura.base_iva_5 > 0:
        totales_data.append(fila_total(f'Base IVA 5%:', _fmt(factura.base_iva_5)))
        totales_data.append(fila_total(f'IVA 5%:', _fmt(factura.valor_iva_5)))

    totales_data.append(fila_total('Total Bruto:', _fmt(
        float(factura.subtotal) + float(factura.valor_iva_total)
    )))

    if factura.valor_retefuente > 0:
        totales_data.append(fila_total(
            f'(-) Retefuente {_pct(factura.retefuente_pct)}:',
            f'- {_fmt(factura.valor_retefuente)}', color=ROJO_VOLCANO
        ))

    if factura.valor_reteiva > 0:
        totales_data.append(fila_total(
            f'(-) ReteIVA {_pct(factura.reteiva_pct)}:',
            f'- {_fmt(factura.valor_reteiva)}', color=ROJO_VOLCANO
        ))

    if factura.valor_reteica > 0:
        totales_data.append(fila_total(
            f'(-) ReteICA {factura.reteica_pct}‰:',
            f'- {_fmt(factura.valor_reteica)}', color=ROJO_VOLCANO
        ))

    if factura.total_retenciones > 0:
        totales_data.append(fila_total(
            'Total Retenciones:', f'- {_fmt(factura.total_retenciones)}',
            color=ROJO_VOLCANO
        ))

    # Línea separadora
    totales_data.append([
        HRFlowable(width='100%', thickness=1.5, color=ROJO_VOLCANO),
        HRFlowable(width='100%', thickness=1.5, color=ROJO_VOLCANO),
    ])

    totales_data.append([
        Paragraph('<b>TOTAL A PAGAR:</b>', style('tp', fontSize=11,
                  fontName='Helvetica-Bold', textColor=ROJO_VOLCANO, alignment=TA_RIGHT)),
        Paragraph(f'<b>{_fmt(factura.total_a_pagar)}</b>', style('tv2', fontSize=11,
                  fontName='Helvetica-Bold', textColor=ROJO_VOLCANO, alignment=TA_RIGHT)),
    ])

    totales_table = Table(
        totales_data,
        colWidths=[W * 0.55, W * 0.45],
        hAlign='RIGHT',
    )
    totales_table.setStyle(TableStyle([
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ('BACKGROUND',    (0, -1), (-1, -1), GRIS_CLARO),
        ('BOX',           (0, -1), (-1, -1), 1, ROJO_VOLCANO),
    ]))

    # Centrar totales a la derecha
    totales_wrapper = Table(
        [[Spacer(W*0.35, 1), totales_table]],
        colWidths=[W * 0.35, W * 0.65],
    )
    elements.append(totales_wrapper)
    elements.append(Spacer(1, 4*mm))

    # ── NOTAS ─────────────────────────────────────────────────────────────────
    if factura.notas:
        elements.append(Paragraph(f'<b>Notas:</b> {factura.notas}', s_small))
        elements.append(Spacer(1, 3*mm))

    # ── PIE DE PÁGINA ─────────────────────────────────────────────────────────
    elements.append(HRFlowable(width='100%', thickness=0.5, color=GRIS_MEDIO))
    elements.append(Spacer(1, 2*mm))

    cufe_text = (
        f'CUFE: {factura.cufe}' if factura.cufe
        else 'CUFE: Pendiente — Factura no enviada a la DIAN'
    )
    elements.append(Paragraph(cufe_text, style('cufe', fontSize=6,
                    textColor=GRIS_MEDIO, alignment=TA_CENTER)))
    elements.append(Spacer(1, 1*mm))
    elements.append(Paragraph(
        f'Generado por ERG Inventory · {razon} · NIT {nit}',
        style('footer', fontSize=6, textColor=GRIS_MEDIO, alignment=TA_CENTER)
    ))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes