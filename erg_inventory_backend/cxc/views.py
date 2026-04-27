from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from core.mixins import CreatedByMixin
from .models import CuentaPorCobrar, PagoCXC
from .serializers import CXCSerializer, PagoCXCSerializer


class CXCListCreateView(CreatedByMixin, generics.ListCreateAPIView):
    queryset           = CuentaPorCobrar.objects.select_related('cliente', 'creado_por').prefetch_related('pagos').all()
    serializer_class   = CXCSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['cliente__nombre', 'concepto', 'estado']
    ordering_fields    = ['fecha_emision', 'fecha_vencimiento', 'monto_total', 'saldo']


class CXCDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = CuentaPorCobrar.objects.all()
    serializer_class   = CXCSerializer
    permission_classes = [IsAuthenticated]


class PagoCXCCreateView(CreatedByMixin, generics.CreateAPIView):
    queryset           = PagoCXC.objects.all()
    serializer_class   = PagoCXCSerializer
    permission_classes = [IsAuthenticated]
