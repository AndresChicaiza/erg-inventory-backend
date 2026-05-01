from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from core.permissions import CanMovimientoInventario
from .models import Movimiento
from .serializers import MovimientoSerializer


class MovimientoListCreateView(generics.ListCreateAPIView):
    queryset           = Movimiento.objects.select_related('producto', 'creado_por').all()
    serializer_class   = MovimientoSerializer
    permission_classes = [CanMovimientoInventario]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['producto__nombre', 'tipo', 'referencia']
    ordering_fields    = ['fecha', 'tipo']

    @transaction.atomic
    def perform_create(self, serializer):
        mov      = serializer.save(creado_por=self.request.user)
        producto = mov.producto

        if mov.tipo == 'Entrada':
            producto.stock += mov.cantidad
        elif mov.tipo == 'Salida':
            producto.stock = max(0, producto.stock - mov.cantidad)
        elif mov.tipo == 'Ajuste':
            producto.stock = mov.cantidad

        producto.save(update_fields=['stock'])


class MovimientoDetailView(generics.RetrieveAPIView):
    queryset           = Movimiento.objects.select_related('producto').all()
    serializer_class   = MovimientoSerializer
    permission_classes = [IsAuthenticated]