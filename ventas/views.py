from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from core.mixins import CreatedByMixin
from .models import Venta
from .serializers import VentaSerializer


class VentaListCreateView(CreatedByMixin, generics.ListCreateAPIView):
    queryset = Venta.objects.select_related('cliente', 'producto', 'creado_por').all()
    serializer_class   = VentaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['cliente__nombre', 'producto__nombre', 'estado']
    ordering_fields    = ['fecha', 'total', 'estado']


class VentaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Venta.objects.select_related('cliente', 'producto').all()
    serializer_class   = VentaSerializer
    permission_classes = [IsAuthenticated]
