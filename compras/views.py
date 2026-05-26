from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from core.mixins import CreatedByMixin
from core.permissions import CanCreateOC, CanAprobarOC, CanRecibirOC
from .models import Compra
from .serializers import CompraSerializer


class CompraListCreateView(CreatedByMixin, generics.ListCreateAPIView):
    queryset = Compra.objects.select_related('proveedor', 'creado_por').prefetch_related('detalles__producto').all()
    serializer_class   = CompraSerializer
    permission_classes = [CanCreateOC]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['proveedor__razon_social', 'producto__nombre', 'estado']
    ordering_fields    = ['fecha', 'total', 'estado']


class CompraDetailView(generics.RetrieveUpdateAPIView):
    queryset           = Compra.objects.select_related('proveedor').prefetch_related('detalles__producto').all()
    serializer_class   = CompraSerializer
    permission_classes = [CanCreateOC]


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db import transaction

class RecibirCompraView(APIView):
    """
    POST /api/compras/<id>/recibir/
    Payload:
    {
      "lotes": {
         "id_detalle_1": { "numero_lote": "L001", "fecha_vencimiento": "2027-12-31" }
      }
    }
    """
    permission_classes = [CanRecibirOC]

    @transaction.atomic
    def post(self, request, pk):
        try:
            compra = Compra.objects.get(pk=pk)
        except Compra.DoesNotExist:
            return Response({'error': 'Compra no encontrada'}, status=404)

        if compra.estado == 'Recibida':
            return Response({'error': 'La compra ya ha sido recibida previamente.'}, status=400)
        
        if compra.estado == 'Cancelada':
            return Response({'error': 'No se puede recibir una compra cancelada.'}, status=400)

        lotes_data = request.data.get('lotes', {})

        from movimientos.models import Movimiento
        from productos.models import Lote

        for detalle in compra.detalles.all():
            producto = detalle.producto
            cantidad = detalle.cantidad
            
            lote_obj = None

            if producto.controla_vencimiento:
                lote_info = lotes_data.get(str(detalle.id))
                if not lote_info or not lote_info.get('numero_lote') or not lote_info.get('fecha_vencimiento'):
                    raise ValidationError(f"Falta información de lote para el producto: {producto.nombre}")
                
                num_lote = lote_info['numero_lote']
                f_venc = lote_info['fecha_vencimiento']

                # Crear o buscar el lote
                lote_obj, created = Lote.objects.get_or_create(
                    producto=producto, numero_lote=num_lote,
                    defaults={'fecha_vencimiento': f_venc}
                )
                lote_obj.stock_disponible += cantidad
                lote_obj.save()

            # Registrar el movimiento
            Movimiento.objects.create(
                producto=producto,
                lote=lote_obj,
                tipo='Entrada',
                cantidad=cantidad,
                referencia=f"OC-{compra.id:04d}",
                observacion=f"Recepción de compra {compra.proveedor.razon_social}",
                creado_por=request.user
            )

            # Actualizar stock general del producto
            producto.stock += cantidad
            producto.save(update_fields=['stock'])

        # Marcar la orden como recibida
        from django.utils import timezone
        import datetime

        hoy = timezone.now().date()

        # Calcular fecha de vencimiento del pago
        condicion = compra.condicion_pago
        if condicion == 'Contado':
            dias = 0
        else:
            dias = int(condicion.replace('_dias', ''))

        fecha_venc_pago = hoy + datetime.timedelta(days=dias)
        compra.estado = 'Recibida'
        compra.fecha_vencimiento_pago = fecha_venc_pago
        compra.save(update_fields=['estado', 'fecha_vencimiento_pago'])

        # ── Auto-generar Cuenta por Pagar ──
        from cxp.models import CuentaPorPagar
        cxp_estado_inicial = 'Pendiente'
        cxp = CuentaPorPagar.objects.create(
            proveedor=compra.proveedor,
            compra=compra,
            concepto=f'OC-{compra.id:04d} - {compra.condicion_pago.replace("_dias", " días")} — {compra.proveedor.razon_social}',
            monto_total=compra.total,
            fecha_vencimiento=fecha_venc_pago,
            notas=compra.notas,
            creado_por=request.user
        )

        # Si es de contado, el usuario pagará en efectivo; dejamos pendiente para que registren el pago.
        return Response({
            'status': 'ok',
            'message': 'Compra recibida e inventario actualizado.',
            'cxp_id': cxp.id,
            'fecha_vencimiento_pago': str(fecha_venc_pago),
        })


class CancelarCompraView(APIView):
    """POST /api/compras/<id>/cancelar/"""
    permission_classes = [CanCreateOC]

    def post(self, request, pk):
        try:
            compra = Compra.objects.get(pk=pk)
        except Compra.DoesNotExist:
            return Response({'error': 'Orden de compra no encontrada'}, status=404)

        if compra.estado == 'Cancelada':
            return Response({'error': 'La orden de compra ya está cancelada'}, status=400)
            
        if compra.estado == 'Recibida':
            return Response({'error': 'No se puede cancelar una orden de compra ya Recibida.'}, status=400)

        compra.estado = 'Cancelada'
        compra.save(update_fields=['estado'])
        
        # Registrar acción en auditoría
        from core.utils import log_action
        log_action(
            user=request.user,
            action='UPDATE',
            modulo='Compras',
            modelo='Compra',
            objeto_id=compra.id,
            descripcion=f"Orden de compra cancelada: OC-{compra.id:04d}",
            request=request
        )

        return Response({'mensaje': 'Orden de compra cancelada correctamente'})
