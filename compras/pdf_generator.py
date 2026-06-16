"""
Generador de PDF para Órdenes de Compra.
Formato operativo interno — Suministros Dacar S.A.S. (VOLCANO ASADORES)
"""
import os
import io
from decimal import Decimal

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
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
AZUL_OC      = HexColor('#1E3A5F')
BLANCO       = white


def _fmt(valor, moneda='COP'):
    """Formatea un número como moneda."""
    try:
        v = Decimal(str(valor))
        simbolo = '$' if moneda == 'COP' else 'USD'
        return f'{simbolo} {v:,.0f}'.replace(',', '.')
    except Exception:
        return f'$ {valor}'


def _pct(valor):
    try:
        return f'{Decimal(str(valor)):.0f}%'
    except Exception:
        return f'{valor}%'


def generar_pdf_orden_compra(compra):
    """
    Genera el PDF de una Orden de Compra y retorna los bytes.
    """
    from configuracion.models import ConfiguracionEmpresa
    config    = ConfiguracionEmpresa.objects.first()
    proveedor = compra.proveedor

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=10*mm,  bottomMargin=15*mm,
    )

    W      = A4[0] - 30*mm
    styles = getSampleStyleSheet()

    def style(name, **kwargs):
        return ParagraphStyle(name, parent=styles['Normal'], **kwargs)

    s_titulo   = style('titulo',  fontSize=8,  textColor=GRIS_OSCURO, leading=10)
    s_bold     = style('bold',    fontSize=8,  textColor=GRIS_OSCURO, fontName='Helvetica-Bold', leading=10)
    s_small    = style('small',   fontSize=7,  textColor=GRIS_MEDIO,  leading=9)
    s_center   = style('center',  fontSize=8,  textColor=GRIS_OSCURO, alignment=TA_CENTER, leading=10)
    s_right    = style('right',   fontSize=8,  textColor=GRIS_OSCURO, alignment=TA_RIGHT,  leading=10)
    s_bold_r   = style('boldr',   fontSize=8,  textColor=GRIS_OSCURO, fontName='Helvetica-Bold', alignment=TA_RIGHT, leading=10)
    s_blue     = style('blue',    fontSize=12, textColor=AZUL_OC,     fontName='Helvetica-Bold', alignment=TA_CENTER, leading=14)

    elements = []

    # ── Datos empresa ─────────────────────────────────────────────────────────
    logo_path  = config.logo.path if (config and config.logo) else None
    nombre_com = config.nombre_comercial if config else 'VOLCANO ASADORES'
    razon      = config.razon_social     if config else 'SUMINISTROS DACAR S.A.S.'
    nit        = f'{config.nit}-{config.digito_verificacion}' if config else '901.334.172-0'
    direccion  = config.direccion        if config else 'CR 17 G # 25 – 78'
    ciudad     = f'{config.ciudad}, {config.departamento}' if config else 'Cali, Valle del Cauca'
    telefono   = config.telefono         if config else '316 691 4910'
    email_emp  = config.email            if config else 'suministrosdacar@gmail.com'
    moneda     = compra.moneda or 'COP'

    # ── ENCABEZADO ────────────────────────────────────────────────────────────
    if logo_path and os.path.exists(logo_path):
        logo_cell = Image(logo_path, width=45*mm, height=18*mm, kind='proportional')
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
    ]

    oc_numero = f'OC-{compra.id:04d}'
    fecha_emision = compra.fecha.strftime('%d/%m/%Y') if compra.fecha else '—'
    fecha_entrega = compra.fecha_esperada_entrega.strftime('%d/%m/%Y') if compra.fecha_esperada_entrega else '—'

    oc_col = [
        Paragraph('<b>ORDEN DE COMPRA</b>', style('oc_t', fontSize=12,
                  textColor=AZUL_OC, fontName='Helvetica-Bold',
                  alignment=TA_CENTER, leading=14)),
        Spacer(1, 2*mm),
        Paragraph(f'<b>{oc_numero}</b>', style('oc_n', fontSize=11,
                  fontName='Helvetica-Bold', alignment=TA_CENTER, leading=13)),
        Spacer(1, 3*mm),
        Paragraph(f'Fecha de emisión: {fecha_emision}', s_center),
        Paragraph(f'Entrega esperada: {fecha_entrega}', s_center),
        Spacer(1, 2*mm),
        Paragraph(f'Moneda: <b>{moneda}</b>', s_center),
        Paragraph(f'Cond. Pago: <b>{compra.condicion_pago.replace("_dias"," días")}</b>', s_center),
    ]

    header_table = Table(
        [[empresa_col, oc_col]],
        colWidths=[W * 0.58, W * 0.42],
    )
    header_table.setStyle(TableStyle([
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW',    (0, 0), (-1, -1), 0.5, AZUL_OC),
        ('RIGHTPADDING', (0, 0), (0, -1), 8),
        ('LEFTPADDING',  (1, 0), (1, -1), 8),
        ('BACKGROUND',   (1, 0), (1, -1), GRIS_CLARO),
        ('BOX',          (1, 0), (1, -1), 0.5, AZUL_OC),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 4*mm))

    # ── DATOS DEL PROVEEDOR ───────────────────────────────────────────────────
    dv = f'-{proveedor.digito_verificacion}' if proveedor.digito_verificacion else ''
    prov_data = [
        [Paragraph('<b>DATOS DEL PROVEEDOR</b>', style('ph', fontSize=8,
                   fontName='Helvetica-Bold', textColor=BLANCO)), '', '', ''],
        ['Razón Social:', Paragraph(f'<b>{proveedor.razon_social}</b>', s_bold),
         'NIT / Doc:', Paragraph(f'<b>{proveedor.numero_documento}{dv}</b>', s_bold)],
        ['Dirección:', Paragraph(proveedor.direccion or '—', s_titulo),
         'Ciudad:', Paragraph(f'{proveedor.ciudad or "—"}, {proveedor.departamento or ""}', s_titulo)],
        ['Teléfono:', Paragraph(proveedor.telefono or '—', s_titulo),
         'Email:', Paragraph(proveedor.email or '—', s_titulo)],
        ['Contacto:', Paragraph(proveedor.contacto or '—', s_titulo),
         'Condición IVA:', Paragraph(proveedor.regimen_tributario.replace('_', ' ').title(), s_titulo)],
    ]

    prov_table = Table(prov_data, colWidths=[W*0.15, W*0.35, W*0.15, W*0.35])
    prov_table.setStyle(TableStyle([
        ('SPAN',         (0, 0), (3, 0)),
        ('BACKGROUND',   (0, 0), (3, 0), AZUL_OC),
        ('TEXTCOLOR',    (0, 0), (3, 0), BLANCO),
        ('FONTNAME',     (0, 0), (3, 0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, -1), 8),
        ('TOPPADDING',   (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        ('LEFTPADDING',  (0, 0), (-1, -1), 4),
        ('GRID',         (0, 1), (-1, -1), 0.3, HexColor('#CCCCCC')),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(prov_table)
    elements.append(Spacer(1, 4*mm))

    # ── TABLA DE PRODUCTOS ────────────────────────────────────────────────────
    items_header = [
        Paragraph('#',           style('h', fontSize=8, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph('Código',      style('h', fontSize=8, fontName='Helvetica-Bold')),
        Paragraph('Descripción', style('h', fontSize=8, fontName='Helvetica-Bold')),
        Paragraph('Cant.',       style('h', fontSize=8, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph('Precio U.',   style('h', fontSize=8, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        Paragraph('% IVA',       style('h', fontSize=8, fontName='Helvetica-Bold', alignment=TA_CENTER)),
        Paragraph('Valor IVA',   style('h', fontSize=8, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        Paragraph('Subtotal',    style('h', fontSize=8, fontName='Helvetica-Bold', alignment=TA_RIGHT)),
    ]

    items_data = [items_header]
    for i, det in enumerate(compra.detalles.all(), start=1):
        items_data.append([
            Paragraph(str(i),                   s_center),
            Paragraph(det.producto.codigo or '', s_titulo),
            Paragraph(det.producto.nombre,       s_titulo),
            Paragraph(f'{det.cantidad:g}',       s_center),
            Paragraph(_fmt(det.precio_unitario, moneda), s_right),
            Paragraph(_pct(det.porcentaje_iva),  s_center),
            Paragraph(_fmt(det.valor_iva, moneda), s_right),
            Paragraph(_fmt(det.subtotal, moneda), s_right),
        ])

    items_table = Table(
        items_data,
        colWidths=[W*0.04, W*0.10, W*0.28, W*0.07, W*0.13, W*0.08, W*0.13, W*0.13],
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
        ('LINEBELOW',     (0, 0), (-1, 0), 1, AZUL_OC),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 4*mm))

    # ── TOTALES ───────────────────────────────────────────────────────────────
    def fila_total(label, valor, bold=False, color=NEGRO):
        return [
            Paragraph(label, style('tl', fontSize=8, textColor=color,
                      fontName='Helvetica-Bold' if bold else 'Helvetica',
                      alignment=TA_RIGHT)),
            Paragraph(valor, style('tv', fontSize=8, textColor=color,
                      fontName='Helvetica-Bold' if bold else 'Helvetica',
                      alignment=TA_RIGHT)),
        ]

    totales_data = [
        fila_total('Subtotal (sin IVA):', _fmt(compra.subtotal, moneda)),
        fila_total(f'Total IVA:',         _fmt(compra.total_iva, moneda)),
        [HRFlowable(width='100%', thickness=1.5, color=AZUL_OC),
         HRFlowable(width='100%', thickness=1.5, color=AZUL_OC)],
    ]
    totales_data.append([
        Paragraph('<b>TOTAL ORDEN:</b>', style('tp', fontSize=11,
                  fontName='Helvetica-Bold', textColor=AZUL_OC, alignment=TA_RIGHT)),
        Paragraph(f'<b>{_fmt(compra.total, moneda)}</b>', style('tv2', fontSize=11,
                  fontName='Helvetica-Bold', textColor=AZUL_OC, alignment=TA_RIGHT)),
    ])

    totales_table = Table(totales_data, colWidths=[W*0.55, W*0.45], hAlign='RIGHT')
    totales_table.setStyle(TableStyle([
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
        ('BACKGROUND',    (0, -1), (-1, -1), GRIS_CLARO),
        ('BOX',           (0, -1), (-1, -1), 1, AZUL_OC),
    ]))
    totales_wrapper = Table([[Spacer(W*0.35, 1), totales_table]], colWidths=[W*0.35, W*0.65])
    elements.append(totales_wrapper)
    elements.append(Spacer(1, 4*mm))

    # ── BODEGA Y NOTAS ────────────────────────────────────────────────────────
    if compra.bodega_destino:
        elements.append(Paragraph(
            f'<b>Bodega de destino:</b> {compra.bodega_destino.nombre} ({compra.bodega_destino.codigo})',
            s_titulo))
        elements.append(Spacer(1, 2*mm))

    if compra.notas:
        elements.append(Paragraph(f'<b>Notas / Instrucciones:</b> {compra.notas}', s_small))
        elements.append(Spacer(1, 3*mm))

    # ── PIE ───────────────────────────────────────────────────────────────────
    elements.append(HRFlowable(width='100%', thickness=0.5, color=GRIS_MEDIO))
    elements.append(Spacer(1, 2*mm))
    elements.append(Paragraph(
        f'Documento generado por ERG Inventory · {razon} · NIT {nit}',
        style('footer', fontSize=6, textColor=GRIS_MEDIO, alignment=TA_CENTER)
    ))
    elements.append(Paragraph(
        'Este documento es una Orden de Compra interna y no tiene carácter fiscal según la DIAN.',
        style('footer2', fontSize=6, textColor=GRIS_MEDIO, alignment=TA_CENTER)
    ))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
