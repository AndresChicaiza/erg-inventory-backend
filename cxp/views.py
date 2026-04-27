from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from core.mixins import CreatedByMixin
from .models import CuentaPorPagar, PagoCXP
from .serializers import CXPSerializer, PagoCXPSerializer


class CXPListCreateView(CreatedByMixin, generics.ListCreateAPIView):
    queryset           = CuentaPorPagar.objects.select_related('proveedor', 'creado_por').prefetch_related('pagos').all()
    serializer_class   = CXPSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['proveedor__empresa', 'concepto', 'estado']
    ordering_fields    = ['fecha_emision', 'fecha_vencimiento', 'monto_total', 'saldo']


class CXPDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = CuentaPorPagar.objects.all()
    serializer_class   = CXPSerializer
    permission_classes = [IsAuthenticated]


class PagoCXPCreateView(CreatedByMixin, generics.CreateAPIView):
    queryset           = PagoCXP.objects.all()
    serializer_class   = PagoCXPSerializer
    permission_classes = [IsAuthenticated]
