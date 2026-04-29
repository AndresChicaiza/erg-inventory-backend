from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from core.mixins import CreatedByMixin
from .models import Venta
from .serializers import VentaSerializer
from productos.models import Producto


class VentaListCreateView(CreatedByMixin, generics.ListCreateAPIView):
    queryset           = Venta.objects.select_related('cliente', 'producto', 'bodega', 'creado_por').all()
    serializer_class   = VentaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['cliente__nombre', 'producto__nombre', 'estado']
    ordering_fields    = ['fecha', 'total', 'estado']

    @transaction.atomic
    def perform_create(self, serializer):
        venta = serializer.save(creado_por=self.request.user)
        producto = venta.producto

        # 1. Validar y descontar stock global del producto
        if producto.stock < venta.cantidad:
            raise Exception(f'Stock insuficiente. Disponible: {producto.stock}')
        producto.stock -= venta.cantidad
        producto.save(update_fields=['stock'])

        # 2. Si se eligió bodega, validar y descontar stock de esa bodega
        if venta.bodega_id:
            from bodegas.models import StockBodega
            sb = StockBodega.objects.select_for_update().filter(
                bodega_id=venta.bodega_id,
                producto=producto
            ).first()

            if not sb or sb.cantidad < venta.cantidad:
                disponible = sb.cantidad if sb else 0
                raise Exception(f'Stock insuficiente en bodega "{venta.bodega.nombre}". '
                                f'Disponible: {disponible}')
            sb.cantidad -= venta.cantidad
            sb.save()

        # 3. Registrar movimiento de salida automático
        from movimientos.models import Movimiento
        Movimiento.objects.create(
            producto=producto,
            tipo='Salida',
            cantidad=venta.cantidad,
            referencia=f'V-{venta.id:04d}',
            observacion=(
                f'Salida por venta a {venta.cliente.nombre}'
                + (f' — Bodega: {venta.bodega.nombre}' if venta.bodega else '')
            ),
            creado_por=self.request.user
        )

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VentaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Venta.objects.select_related('cliente', 'producto', 'bodega').all()
    serializer_class   = VentaSerializer
    permission_classes = [IsAuthenticated]