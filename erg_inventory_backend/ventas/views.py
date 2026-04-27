from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from core.mixins import CreatedByMixin
from .models import Venta
from .serializers import VentaSerializer
from productos.models import Producto


class VentaListCreateView(CreatedByMixin, generics.ListCreateAPIView):
    queryset           = Venta.objects.select_related('cliente', 'producto', 'creado_por').all()
    serializer_class   = VentaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['cliente__nombre', 'producto__nombre', 'estado']
    ordering_fields    = ['fecha', 'total', 'estado']

    @transaction.atomic
    def perform_create(self, serializer):
        venta = serializer.save(creado_por=self.request.user)
        # Descontar stock automáticamente al crear una venta
        producto = venta.producto
        if producto.stock < venta.cantidad:
            raise Exception(f'Stock insuficiente. Disponible: {producto.stock}')
        producto.stock -= venta.cantidad
        producto.save(update_fields=['stock'])

        # Registrar movimiento de salida automático
        from movimientos.models import Movimiento
        Movimiento.objects.create(
            producto=producto,
            tipo='Salida',
            cantidad=venta.cantidad,
            referencia=f'V-{venta.id:04d}',
            observacion=f'Salida por venta a {venta.cliente.nombre}',
            creado_por=self.request.user
        )

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VentaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Venta.objects.select_related('cliente', 'producto').all()
    serializer_class   = VentaSerializer
    permission_classes = [IsAuthenticated]
