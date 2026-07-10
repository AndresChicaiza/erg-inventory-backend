from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
import datetime


class ResumenView(APIView):
    """Dashboard general — GET /api/reportes/resumen/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from facturacion.models import Factura
        from compras.models import Compra
        from productos.models import Producto
        from clientes.models import Cliente
        from proveedores.models import Proveedor
        from movimientos.models import Movimiento
        from entregas.models import Entrega

        # Totales monetarios
        total_ventas  = Factura.objects.exclude(estado='Anulada').aggregate(t=Sum('total_a_pagar'))['t']  or 0
        total_compras = Compra.objects.exclude(estado='Anulada').aggregate(t=Sum('total'))['t'] or 0

        # Ventas por estado
        ventas_estado = (
            Factura.objects.values('estado')
            .annotate(cantidad=Count('id'), monto=Sum('total_a_pagar'))
        )

        # Compras por estado
        compras_estado = (
            Compra.objects.values('estado')
            .annotate(cantidad=Count('id'), monto=Sum('total'))
        )

        # Stock
        stock_bajo   = Producto.objects.filter(stock__gt=0, stock__lte=F('stock_minimo'))
        sin_stock    = Producto.objects.filter(stock=0)
        top_stock    = (
            Producto.objects
            .filter(estado='Activo')
            .order_by('-stock')[:5]
            .values('nombre', 'stock', 'categoria')
        )

        # Movimientos por tipo
        movs_tipo = (
            Movimiento.objects.values('tipo')
            .annotate(cantidad=Count('id'))
        )

        # Entregas por estado
        entregas_estado = (
            Entrega.objects.values('estado')
            .annotate(cantidad=Count('id'))
        )

        return Response({
            # Monetarios
            'total_ventas':  float(total_ventas),
            'total_compras': float(total_compras),
            'utilidad_bruta': float(total_ventas - total_compras),

            # Conteos generales
            'num_ventas':      Factura.objects.count(),
            'num_compras':     Compra.objects.count(),
            'num_productos':   Producto.objects.count(),
            'num_clientes':    Cliente.objects.count(),
            'num_proveedores': Proveedor.objects.count(),
            'num_movimientos': Movimiento.objects.count(),

            # Stock
            'productos_stock_bajo': stock_bajo.count(),
            'productos_sin_stock':  sin_stock.count(),
            'top_stock': list(top_stock),

            # Detalles por estado
            'ventas_por_estado':    list(ventas_estado),
            'compras_por_estado':   list(compras_estado),
            'entregas_por_estado':  list(entregas_estado),
            'movimientos_por_tipo': list(movs_tipo),
        })


class AlertasView(APIView):
    """GET /api/reportes/alertas/ — KPIs y alertas urgentes para el dashboard."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from facturacion.models import Factura
        from compras.models import Compra
        from productos.models import Producto, Lote
        from entregas.models import Entrega
        from cxc.models import CuentaPorCobrar
        from cxp.models import CuentaPorPagar

        hoy   = timezone.now().date()
        hoy_dt_inicio = timezone.make_aware(datetime.datetime.combine(hoy, datetime.time.min))
        hoy_dt_fin    = timezone.make_aware(datetime.datetime.combine(hoy, datetime.time.max))
        inicio_mes    = hoy.replace(day=1)
        d30           = hoy + datetime.timedelta(days=30)

        # ── Ventas ──────────────────────────────────────────────
        facturas_hoy = Factura.objects.filter(
            fecha_emision=hoy, estado__in=['Emitida', 'Pagada']
        )
        ventas_hoy   = facturas_hoy.aggregate(t=Sum('total_a_pagar'))['t'] or 0
        num_fact_hoy = facturas_hoy.count()

        facturas_mes = Factura.objects.filter(
            fecha_emision__gte=inicio_mes, estado__in=['Emitida', 'Pagada']
        )
        ventas_mes   = facturas_mes.aggregate(t=Sum('total_a_pagar'))['t'] or 0
        num_fact_mes = facturas_mes.count()

        # Histórico de últimos 7 días para gráfico
        historico_7dias = []
        for i in range(6, -1, -1):
            dia_iter = hoy - datetime.timedelta(days=i)
            tot_dia = Factura.objects.filter(
                fecha_emision=dia_iter, estado__in=['Emitida', 'Pagada']
            ).aggregate(t=Sum('total_a_pagar'))['t'] or 0
            historico_7dias.append({
                'fecha': dia_iter.strftime('%d/%m'),
                'ventas': float(tot_dia)
            })

        # ── Stock ───────────────────────────────────────────────
        sin_stock   = Producto.objects.filter(stock=0, estado='Activo')
        stock_bajo  = Producto.objects.filter(stock__gt=0, stock__lte=F('stock_minimo'), estado='Activo')

        # ── Lotes por vencer (<= 30 días) ───────────────────────
        lotes_pv = Lote.objects.filter(
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=d30,
            stock_disponible__gt=0
        ).select_related('producto').order_by('fecha_vencimiento')[:10]

        # Lotes vencidos con stock
        lotes_vencidos = Lote.objects.filter(
            fecha_vencimiento__lt=hoy,
            stock_disponible__gt=0
        ).count()

        # ── Órdenes de Compra pendientes ─────────────────────────
        oc_pendientes = Compra.objects.filter(estado__in=['Pendiente', 'Aprobada']).count()

        # ── Entregas pendientes ───────────────────────────────────
        entregas_pend = Entrega.objects.filter(estado__in=['Pendiente', 'Asignada']).count()

        # ── CXC vencidas ─────────────────────────────────────────
        cxc_vencidas = CuentaPorCobrar.objects.filter(
            fecha_vencimiento__lt=hoy,
            estado__in=['Pendiente', 'Parcial', 'Vencida']
        )
        cxc_vencidas_monto = cxc_vencidas.aggregate(t=Sum('saldo'))['t'] or 0

        # ── CXP vencidas ─────────────────────────────────────────
        cxp_vencidas = CuentaPorPagar.objects.filter(
            fecha_vencimiento__lt=hoy,
            estado__in=['Pendiente', 'Parcial', 'Vencida']
        )
        cxp_vencidas_monto = cxp_vencidas.aggregate(t=Sum('saldo'))['t'] or 0

        # ── Top 5 productos sin stock ─────────────────────────────
        top_sin_stock = list(
            sin_stock.values('nombre', 'categoria', 'stock_minimo')[:5]
        )

        # ── Top 5 stock bajo ─────────────────────────────────────
        top_stock_bajo = list(
            stock_bajo.values('nombre', 'stock', 'stock_minimo', 'categoria')
            .order_by('stock')[:5]
        )

        # ── Marketplace pendientes ─────────────────────────────────────
        try:
            from marketplace.models import PedidoOnline
            marketplace_pendientes = PedidoOnline.objects.filter(
                estado__in=['Pendiente', 'En_Revision']
            ).count()
        except Exception:
            marketplace_pendientes = 0

        # ── KPIs Producción ────────────────────────────────────────────
        try:
            from produccion.models import OrdenProduccion, ConsumoProduccion
            ordenes_retrasadas = OrdenProduccion.objects.filter(
                estado__in=['Pendiente', 'En_Proceso'],
                creado_en__lt=timezone.now() - datetime.timedelta(days=3)
            ).count()
            
            consumos_recientes = ConsumoProduccion.objects.filter(
                orden__actualizado_en__gte=timezone.make_aware(datetime.datetime.combine(inicio_mes, datetime.time.min))
            )
            total_mermas = 0
            for c in consumos_recientes:
                if c.cantidad_real > c.cantidad_esperada:
                    total_mermas += float(c.cantidad_real - c.cantidad_esperada)
                    
            ords_mes = OrdenProduccion.objects.filter(
                actualizado_en__gte=timezone.make_aware(datetime.datetime.combine(inicio_mes, datetime.time.min))
            )
            completadas = ords_mes.filter(estado='Completada').count()
            total_ords = ords_mes.count()
            eficiencia = round((completadas / total_ords * 100) if total_ords > 0 else 100, 1)

            produccion_data = {
                'ordenes_retrasadas': ordenes_retrasadas,
                'total_mermas': round(total_mermas, 2),
                'eficiencia': eficiencia
            }
        except Exception:
            produccion_data = {
                'ordenes_retrasadas': 0, 'total_mermas': 0, 'eficiencia': 100
            }

        return Response({
            'ventas': {
                'hoy':          float(ventas_hoy),
                'num_hoy':      num_fact_hoy,
                'mes':          float(ventas_mes),
                'num_mes':      num_fact_mes,
                'historico':    historico_7dias,
            },
            'stock': {
                'sin_stock':    sin_stock.count(),
                'stock_bajo':   stock_bajo.count(),
                'top_sin_stock':    top_sin_stock,
                'top_stock_bajo':   top_stock_bajo,
            },
            'lotes': {
                'por_vencer':   lotes_pv.count(),
                'vencidos':     lotes_vencidos,
                'proximos': [
                    {
                        'producto': l.producto.nombre,
                        'lote': l.numero_lote,
                        'vence': str(l.fecha_vencimiento),
                        'dias': (l.fecha_vencimiento - hoy).days,
                        'stock': l.stock_disponible,
                    }
                    for l in lotes_pv
                ],
            },
            'operaciones': {
                'oc_pendientes':    oc_pendientes,
                'entregas_pend':    entregas_pend,
            },
            'financiero': {
                'cxc_vencidas':     cxc_vencidas.count(),
                'cxc_monto':        float(cxc_vencidas_monto),
                'cxp_vencidas':     cxp_vencidas.count(),
                'cxp_monto':        float(cxp_vencidas_monto),
            },
            'marketplace': {
                'pedidos_pendientes': marketplace_pendientes,
            },
            'produccion': produccion_data,
        })


class FlujoCajaView(APIView):
    """GET /api/reportes/flujo-caja/ — resumen financiero cruzado de CXC y CXP"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from cxc.models import CuentaPorCobrar
        from cxp.models import CuentaPorPagar

        hoy  = timezone.now().date()
        d7   = hoy + datetime.timedelta(days=7)
        d30  = hoy + datetime.timedelta(days=30)

        # ── CXC (por cobrar) ──
        cxc_qs = CuentaPorCobrar.objects.exclude(estado__in=['Pagada', 'Anulada'])
        cxc_total   = cxc_qs.aggregate(t=Sum('saldo'))['t'] or 0
        cxc_vencida = cxc_qs.filter(fecha_vencimiento__lt=hoy).aggregate(t=Sum('saldo'))['t'] or 0
        cxc_semana  = cxc_qs.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=d7).aggregate(t=Sum('saldo'))['t'] or 0
        cxc_mes     = cxc_qs.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=d30).aggregate(t=Sum('saldo'))['t'] or 0

        # ── CXP (por pagar) ──
        cxp_qs = CuentaPorPagar.objects.exclude(estado__in=['Pagada', 'Anulada'])
        cxp_total   = cxp_qs.aggregate(t=Sum('saldo'))['t'] or 0
        cxp_vencida = cxp_qs.filter(fecha_vencimiento__lt=hoy).aggregate(t=Sum('saldo'))['t'] or 0
        cxp_semana  = cxp_qs.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=d7).aggregate(t=Sum('saldo'))['t'] or 0
        cxp_mes     = cxp_qs.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=d30).aggregate(t=Sum('saldo'))['t'] or 0

        top_clientes = list(
            cxc_qs.values('cliente__razon_social')
            .annotate(saldo_total=Sum('saldo'))
            .order_by('-saldo_total')[:5]
        )
        top_proveedores = list(
            cxp_qs.values('proveedor__razon_social')
            .annotate(saldo_total=Sum('saldo'))
            .order_by('-saldo_total')[:5]
        )

        return Response({
            'cxc': {
                'total_pendiente': float(cxc_total),
                'vencida':         float(cxc_vencida),
                'proxima_semana':  float(cxc_semana),
                'proximo_mes':     float(cxc_mes),
                'num_cuentas':     cxc_qs.count(),
            },
            'cxp': {
                'total_pendiente': float(cxp_total),
                'vencida':         float(cxp_vencida),
                'proxima_semana':  float(cxp_semana),
                'proximo_mes':     float(cxp_mes),
                'num_cuentas':     cxp_qs.count(),
            },
            'posicion_neta':   float(cxc_total) - float(cxp_total),
            'top_clientes':    top_clientes,
            'top_proveedores': top_proveedores,
        })


class ExportarNominaView(APIView):
    """GET /api/reportes/exportar/nomina/<periodo_id>/ — exporta nómina a PDF."""
    permission_classes = [IsAuthenticated]

    def get(self, request, periodo_id):
        from nomina.models import PeriodoNomina
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        import io
        from django.http import HttpResponse

        try:
            periodo = PeriodoNomina.objects.prefetch_related('lineas__empleado').get(pk=periodo_id)
        except PeriodoNomina.DoesNotExist:
            return Response({'error': 'Período no encontrado'}, status=404)

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(letter),
                                leftMargin=1.5*cm, rightMargin=1.5*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story  = []

        # Título
        story.append(Paragraph(f'<b>NÓMINA — {periodo.nombre.upper()}</b>', styles['Title']))
        story.append(Paragraph(f'{periodo.fecha_inicio} al {periodo.fecha_fin} | Estado: {periodo.estado}', styles['Normal']))
        story.append(Spacer(1, 0.5*cm))

        # Tabla
        headers = ['Empleado', 'Cargo', 'Días', 'Salario Base', 'Aux. Tpte', 'Extras',
                   'Total Dev.', 'Salud', 'Pensión', 'Otras Ded.', 'NETO']
        data = [headers]
        for l in periodo.lineas.all():
            data.append([
                l.empleado.nombre,
                l.empleado.cargo,
                str(l.dias_trabajados),
                f'${float(l.salario_base):,.0f}',
                f'${float(l.auxilio_transporte or 0):,.0f}',
                f'${float(l.horas_extra or 0) + float(l.bonificaciones or 0):,.0f}',
                f'${float(l.total_devengado):,.0f}',
                f'${float(l.salud or 0):,.0f}',
                f'${float(l.pension or 0):,.0f}',
                f'${float(l.otras_deducciones or 0) + float(l.retencion_fuente or 0):,.0f}',
                f'${float(l.neto_pagar):,.0f}',
            ])

        # Totales
        data.append([
            'TOTALES', '', '', '', '', '',
            f'${float(periodo.total_devengado):,.0f}', '', '',
            f'${float(periodo.total_deducciones):,.0f}',
            f'${float(periodo.total_neto):,.0f}',
        ])

        t = Table(data, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),  (-1,0),  colors.HexColor('#4f46e5')),
            ('TEXTCOLOR',     (0,0),  (-1,0),  colors.white),
            ('FONTNAME',      (0,0),  (-1,0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0,0),  (-1,-1), 8),
            ('ALIGN',         (2,0),  (-1,-1), 'RIGHT'),
            ('ROWBACKGROUNDS',(0,1),  (-1,-2), [colors.white, colors.HexColor('#f8fafc')]),
            ('BACKGROUND',    (0,-1), (-1,-1), colors.HexColor('#1e293b')),
            ('TEXTCOLOR',     (0,-1), (-1,-1), colors.white),
            ('FONTNAME',      (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('GRID',          (0,0),  (-1,-1), 0.25, colors.HexColor('#e2e8f0')),
            ('TOPPADDING',    (0,0),  (-1,-1), 4),
            ('BOTTOMPADDING', (0,0),  (-1,-1), 4),
        ]))
        story.append(t)

        doc.build(story)
        buf.seek(0)
        resp = HttpResponse(buf, content_type='application/pdf')
        resp['Content-Disposition'] = f'attachment; filename="nomina_{periodo_id}.pdf"'
        return resp


class ExportarCXCView(APIView):
    """GET /api/reportes/exportar/cxc/ — exporta CXC pendiente a PDF."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from cxc.models import CuentaPorCobrar
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        import io
        from django.http import HttpResponse

        cuentas = CuentaPorCobrar.objects.exclude(
            estado__in=['Pagada', 'Anulada']
        ).select_related('cliente').order_by('fecha_vencimiento')

        buf  = io.BytesIO()
        doc  = SimpleDocTemplate(buf, pagesize=letter,
                                 leftMargin=1.5*cm, rightMargin=1.5*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story  = []

        story.append(Paragraph('<b>CUENTAS POR COBRAR — CARTERA PENDIENTE</b>', styles['Title']))
        story.append(Paragraph(f'Generado: {timezone.now().date()}', styles['Normal']))
        story.append(Spacer(1, 0.4*cm))

        headers = ['#', 'Cliente', 'Concepto', 'Monto Total', 'Pagado', 'Saldo', 'Vence', 'Estado']
        data    = [headers]
        total   = 0
        for i, c in enumerate(cuentas, 1):
            data.append([
                f'CXC-{c.id:04d}', c.cliente.razon_social, c.concepto[:30],
                f'${float(c.monto_total):,.0f}', f'${float(c.monto_pagado):,.0f}',
                f'${float(c.saldo):,.0f}', str(c.fecha_vencimiento), c.estado,
            ])
            total += float(c.saldo)
        data.append(['', '', 'TOTAL CARTERA', '', '', f'${total:,.0f}', '', ''])

        t = Table(data, repeatRows=1, colWidths=[1.5*cm,5*cm,4*cm,2.5*cm,2*cm,2.5*cm,2.5*cm,2*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),  (-1,0),  colors.HexColor('#059669')),
            ('TEXTCOLOR',     (0,0),  (-1,0),  colors.white),
            ('FONTNAME',      (0,0),  (-1,-1), 'Helvetica'),
            ('FONTNAME',      (0,0),  (-1,0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0,0),  (-1,-1), 8),
            ('ROWBACKGROUNDS',(0,1),  (-1,-2), [colors.white, colors.HexColor('#f0fdf4')]),
            ('BACKGROUND',    (0,-1), (-1,-1), colors.HexColor('#065f46')),
            ('TEXTCOLOR',     (0,-1), (-1,-1), colors.white),
            ('FONTNAME',      (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('GRID',          (0,0),  (-1,-1), 0.25, colors.HexColor('#d1fae5')),
            ('TOPPADDING',    (0,0),  (-1,-1), 4),
            ('BOTTOMPADDING', (0,0),  (-1,-1), 4),
        ]))
        story.append(t)
        doc.build(story)
        buf.seek(0)
        resp = HttpResponse(buf, content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="cxc_pendiente.pdf"'
        return resp


class ExportarCXPView(APIView):
    """GET /api/reportes/exportar/cxp/ — exporta CXP pendiente a PDF."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from cxp.models import CuentaPorPagar
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        import io
        from django.http import HttpResponse

        cuentas = CuentaPorPagar.objects.exclude(
            estado__in=['Pagada', 'Anulada']
        ).select_related('proveedor').order_by('fecha_vencimiento')

        buf  = io.BytesIO()
        doc  = SimpleDocTemplate(buf, pagesize=letter,
                                 leftMargin=1.5*cm, rightMargin=1.5*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story  = []

        story.append(Paragraph('<b>CUENTAS POR PAGAR — OBLIGACIONES PENDIENTES</b>', styles['Title']))
        story.append(Paragraph(f'Generado: {timezone.now().date()}', styles['Normal']))
        story.append(Spacer(1, 0.4*cm))

        headers = ['#', 'Proveedor', 'Concepto', 'Monto Total', 'Pagado', 'Saldo', 'Vence', 'Estado']
        data    = [headers]
        total   = 0
        for c in cuentas:
            data.append([
                f'CXP-{c.id:04d}', c.proveedor.razon_social, c.concepto[:30],
                f'${float(c.monto_total):,.0f}', f'${float(c.monto_pagado):,.0f}',
                f'${float(c.saldo):,.0f}', str(c.fecha_vencimiento), c.estado,
            ])
            total += float(c.saldo)
        data.append(['', '', 'TOTAL DEUDA', '', '', f'${total:,.0f}', '', ''])

        t = Table(data, repeatRows=1, colWidths=[1.5*cm,5*cm,4*cm,2.5*cm,2*cm,2.5*cm,2.5*cm,2*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),  (-1,0),  colors.HexColor('#dc2626')),
            ('TEXTCOLOR',     (0,0),  (-1,0),  colors.white),
            ('FONTNAME',      (0,0),  (-1,-1), 'Helvetica'),
            ('FONTNAME',      (0,0),  (-1,0),  'Helvetica-Bold'),
            ('FONTSIZE',      (0,0),  (-1,-1), 8),
            ('ROWBACKGROUNDS',(0,1),  (-1,-2), [colors.white, colors.HexColor('#fef2f2')]),
            ('BACKGROUND',    (0,-1), (-1,-1), colors.HexColor('#7f1d1d')),
            ('TEXTCOLOR',     (0,-1), (-1,-1), colors.white),
            ('FONTNAME',      (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('GRID',          (0,0),  (-1,-1), 0.25, colors.HexColor('#fecaca')),
            ('TOPPADDING',    (0,0),  (-1,-1), 4),
            ('BOTTOMPADDING', (0,0),  (-1,-1), 4),
        ]))
        story.append(t)
        doc.build(story)
        buf.seek(0)
        resp = HttpResponse(buf, content_type='application/pdf')
        resp['Content-Disposition'] = 'attachment; filename="cxp_pendiente.pdf"'
        return resp


class PrediccionStockView(APIView):
    """GET /api/reportes/predicciones-stock/ — Predice el agotamiento de stock usando ML."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .ml_predictor import predecir_agotamiento_stock
        
        # Opcional: recibir parametro de dias desde el frontend
        dias_historial = int(request.GET.get('dias_historial', 90))
        
        try:
            resultados = predecir_agotamiento_stock(dias_historial=dias_historial)
            return Response({'predicciones': resultados})
        except Exception as e:
            return Response({'error': str(e)}, status=500)

