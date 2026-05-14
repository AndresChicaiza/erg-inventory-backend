from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from core.permissions import IsAdminOrContador, CanEmitirFactura
from .models import Factura, DetalleFactura, NotaCredito
from .serializers import (
    FacturaSerializer, FacturaListSerializer,
    DetalleFacturaSerializer, NotaCreditoSerializer,
    CalcularImpuestosSerializer,
)
from .calculadora import calcular_totales_desde_items, calcular_retenciones


class FacturaListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['numero_completo', 'cliente__razon_social',
                          'cliente__numero_documento', 'estado']
    ordering_fields    = ['numero', 'fecha_emision', 'total_a_pagar', 'estado']

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return FacturaListSerializer
        return FacturaSerializer

    def get_queryset(self):
        qs = Factura.objects.select_related('cliente', 'creado_por').all()

        # Marcar automáticamente las vencidas
        hoy = timezone.now().date()
        qs.filter(
            estado__in=['Emitida'],
            fecha_vencimiento__lt=hoy,
        ).update(estado='Vencida')

        # Filtros
        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            qs = qs.filter(fecha_emision__gte=fecha_desde)

        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_hasta:
            qs = qs.filter(fecha_emision__lte=fecha_hasta)

        cliente = self.request.query_params.get('cliente')
        if cliente:
            qs = qs.filter(cliente_id=cliente)

        return qs

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)


class FacturaDetailView(generics.RetrieveUpdateAPIView):
    queryset           = Factura.objects.select_related('cliente').prefetch_related('detalles').all()
    serializer_class   = FacturaSerializer
    permission_classes = [IsAuthenticated]


class DetalleFacturaListCreateView(generics.ListCreateAPIView):
    serializer_class   = DetalleFacturaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DetalleFactura.objects.filter(
            factura_id=self.kwargs['factura_id']
        )

    @transaction.atomic
    def perform_create(self, serializer):
        factura = Factura.objects.get(pk=self.kwargs['factura_id'])
        detalle = serializer.save(factura=factura)
        factura.recalcular_totales()

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        """Eliminar todos los detalles de una factura (para reemplazarlos)."""
        factura_id = self.kwargs['factura_id']
        DetalleFactura.objects.filter(factura_id=factura_id).delete()
        factura = Factura.objects.get(pk=factura_id)
        factura.recalcular_totales()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DetalleFacturaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = DetalleFactura.objects.all()
    serializer_class   = DetalleFacturaSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def perform_destroy(self, instance):
        factura = instance.factura
        instance.delete()
        factura.recalcular_totales()

    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.save()
        instance.factura.recalcular_totales()


class EmitirFacturaView(APIView):
    """POST /api/facturas/<id>/emitir/ — cambia estado a Emitida."""
    permission_classes = [CanEmitirFactura]

    @transaction.atomic
    def post(self, request, pk):
        try:
            factura = Factura.objects.get(pk=pk)
        except Factura.DoesNotExist:
            return Response({'error': 'Factura no encontrada'}, status=404)

        if factura.estado != 'Borrador':
            return Response(
                {'error': f'Solo se pueden emitir facturas en Borrador. Estado actual: {factura.estado}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not factura.detalles.exists():
            return Response(
                {'error': 'La factura no tiene ítems — agrega al menos un producto'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if factura.condicion_pago == 'Contado':
            factura.estado = 'Pagada'
        else:
            factura.estado = 'Emitida'

        factura.emitida_por     = request.user
        factura.fecha_emision_ts = timezone.now()

        # ── Descontar inventario ──
        if factura.bodega:
            from bodegas.models import StockBodega
            from movimientos.models import Movimiento

            for detalle in factura.detalles.all():
                if not detalle.producto:
                    continue  # Si es un ítem manual sin producto, se ignora

                producto = detalle.producto
                cantidad = detalle.cantidad

                from produccion.models import OrdenProduccion
                necesita_produccion = False
                cantidad_a_producir = 0

                # 1. Validar y descontar stock global
                if producto.stock < cantidad:
                    if producto.tipo_inventario == 'TERMINADO' and hasattr(producto, 'receta'):
                        necesita_produccion = True
                        # Producir solo lo que falta (o todo si stock es <= 0)
                        stock_actual = producto.stock if producto.stock > 0 else 0
                        cantidad_a_producir = cantidad - stock_actual
                    else:
                        return Response(
                            {'error': f'Stock global insuficiente para el producto "{producto.nombre}". Disponible: {producto.stock}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                producto.stock -= cantidad
                producto.save(update_fields=['stock'])

                # 2. Validar y descontar stock de bodega
                sb = StockBodega.objects.select_for_update().filter(
                    bodega_id=factura.bodega_id,
                    producto=producto
                ).first()

                if not sb or sb.cantidad < cantidad:
                    if necesita_produccion:
                        if not sb:
                            sb = StockBodega.objects.create(bodega_id=factura.bodega_id, producto=producto, cantidad=0)
                    else:
                        disponible = sb.cantidad if sb else 0
                        return Response(
                            {'error': f'Stock insuficiente en bodega "{factura.bodega.nombre}" para el producto "{producto.nombre}". Disponible: {disponible}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                sb.cantidad -= cantidad
                sb.save()

                # Generar orden de producción si aplica
                if necesita_produccion:
                    orden = OrdenProduccion.objects.create(
                        receta=producto.receta,
                        cantidad_a_fabricar=cantidad_a_producir,
                        bodega_id=factura.bodega_id,
                        factura_vinculada=factura,
                        creado_por=request.user
                    )
                    # Autogenerar consumos esperados
                    from produccion.models import ConsumoProduccion
                    for ingrediente in orden.receta.ingredientes.all():
                        c_esperada = ingrediente.cantidad_esperada * orden.cantidad_a_fabricar
                        ConsumoProduccion.objects.create(
                            orden=orden,
                            producto_materia=ingrediente.producto_materia,
                            cantidad_esperada=c_esperada,
                            cantidad_real=c_esperada
                        )

                # 3. Registrar movimiento de salida
                Movimiento.objects.create(
                    producto=producto,
                    tipo='Salida',
                    cantidad=cantidad,
                    referencia=factura.numero_completo,
                    observacion=f'Salida por emisión de Factura a {factura.cliente.razon_social} — Bodega: {factura.bodega.nombre}',
                    creado_por=request.user
                )

        factura.save(update_fields=['estado', 'emitida_por', 'fecha_emision_ts'])

        # ── Autogenerar Entrega si aplica ──
        if factura.requiere_envio:
            from entregas.models import Entrega, DetalleEntrega
            entrega = Entrega.objects.create(
                factura=factura,
                tipo_entrega='Venta',
                cliente=factura.cliente,
                bodega_origen=factura.bodega,
                direccion=factura.cliente.direccion or '',
                estado='Pendiente',
                creado_por=request.user
            )
            for detalle in factura.detalles.all():
                if detalle.producto:
                    DetalleEntrega.objects.create(
                        entrega=entrega,
                        producto=detalle.producto,
                        cantidad=detalle.cantidad
                    )

        # ── Crear Cuenta por Cobrar si es a crédito ──
        if factura.condicion_pago != 'Contado':
            from cxc.models import CuentaPorCobrar
            CuentaPorCobrar.objects.create(
                cliente=factura.cliente,
                factura=factura,
                concepto=f'Factura {factura.numero_completo} - {factura.condicion_pago.replace("_dias", " días")}',
                monto_total=factura.total_a_pagar,
                fecha_vencimiento=factura.fecha_vencimiento,
                creado_por=request.user
            )

        return Response(FacturaSerializer(factura).data)


class AnularFacturaView(APIView):
    """POST /api/facturas/<id>/anular/"""
    permission_classes = [IsAdminOrContador]

    def post(self, request, pk):
        try:
            factura = Factura.objects.get(pk=pk)
        except Factura.DoesNotExist:
            return Response({'error': 'Factura no encontrada'}, status=404)

        if factura.estado == 'Anulada':
            return Response({'error': 'La factura ya está anulada'}, status=400)

        motivo = request.data.get('motivo', 'Sin motivo especificado')
        factura.estado = 'Anulada'
        factura.notas  = f'{factura.notas}\n[ANULADA] {motivo}'.strip()
        factura.save(update_fields=['estado', 'notas'])

        return Response({'mensaje': 'Factura anulada correctamente'})


class MarcarFacturaPagadaView(APIView):
    """POST /api/facturas/<id>/pagar/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            factura = Factura.objects.get(pk=pk)
        except Factura.DoesNotExist:
            return Response({'error': 'Factura no encontrada'}, status=404)

        if factura.estado not in ['Emitida', 'Vencida']:
            return Response({'error': f'Solo se pueden pagar facturas Emitidas o Vencidas. Estado actual: {factura.estado}'}, status=400)

        factura.estado = 'Pagada'
        factura.save(update_fields=['estado'])

        return Response({'mensaje': 'Factura marcada como pagada correctamente'})


class CalcularImpuestosView(APIView):
    """
    POST /api/facturas/calcular-impuestos/
    Calcula impuestos en tiempo real sin guardar nada.
    Usado por el frontend para mostrar el resumen mientras el usuario edita.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CalcularImpuestosSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data

        try:
            from clientes.models import Cliente
            cliente = Cliente.objects.get(pk=data['cliente_id'])
        except Cliente.DoesNotExist:
            return Response({'error': 'Cliente no encontrado'}, status=404)

        totales     = calcular_totales_desde_items(data['items'])
        retenciones = calcular_retenciones(
            subtotal=totales['subtotal'],
            valor_iva=totales['valor_iva_total'],
            cliente=cliente,
            concepto_retefuente=data['concepto_retefuente'],
        )

        total_a_pagar = (
            totales['bruto_factura'] - retenciones['total_retenciones']
        )

        return Response({
            **totales,
            **retenciones,
            'total_a_pagar': round(total_a_pagar, 2),
            'cliente_agente_retenedor': cliente.agente_retenedor,
            'cliente_gran_contribuyente': cliente.gran_contribuyente,
            'cliente_responsable_iva': cliente.responsable_iva,
        })


class FacturaPDFView(APIView):
    """GET /api/facturas/<id>/pdf/ — genera y devuelve el PDF."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            factura = Factura.objects.select_related('cliente').prefetch_related('detalles').get(pk=pk)
        except Factura.DoesNotExist:
            return Response({'error': 'Factura no encontrada'}, status=404)

        from .pdf_generator import generar_pdf_factura
        from django.http import HttpResponse

        pdf_bytes = generar_pdf_factura(factura)
        response  = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="{factura.numero_completo}.pdf"'
        )
        return response


class ResumenFacturacionView(APIView):
    """GET /api/facturas/resumen/ — totales para el dashboard."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import Sum, Count
        hoy = timezone.now().date()
        qs  = Factura.objects.exclude(estado='Anulada')

        data = {
            'total_emitido_mes': qs.filter(
                fecha_emision__year=hoy.year,
                fecha_emision__month=hoy.month,
                estado__in=['Emitida', 'Pagada'],
            ).aggregate(t=Sum('total_a_pagar'))['t'] or 0,

            'total_pendiente': qs.filter(
                estado='Emitida'
            ).aggregate(t=Sum('total_a_pagar'))['t'] or 0,

            'total_vencido': qs.filter(
                estado='Vencida'
            ).aggregate(t=Sum('total_a_pagar'))['t'] or 0,

            'por_estado': {
                e: qs.filter(estado=e).count()
                for e, _ in Factura.ESTADO_CHOICES
            },
        }
        return Response(data)


class NotaCreditoListCreateView(generics.ListCreateAPIView):
    queryset           = NotaCredito.objects.select_related('factura_original').all()
    serializer_class   = NotaCreditoSerializer
    permission_classes = [IsAdminOrContador]

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)