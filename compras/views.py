from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from core.mixins import CreatedByMixin
from .models import Compra
from .serializers import CompraSerializer


class CompraListCreateView(CreatedByMixin, generics.ListCreateAPIView):
    queryset = Compra.objects.select_related('proveedor', 'producto', 'creado_por').all()
    serializer_class   = CompraSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['proveedor__empresa', 'producto__nombre', 'estado']
    ordering_fields    = ['fecha', 'total', 'estado']


class CompraDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Compra.objects.select_related('proveedor', 'producto').all()
    serializer_class   = CompraSerializer
    permission_classes = [IsAuthenticated]
