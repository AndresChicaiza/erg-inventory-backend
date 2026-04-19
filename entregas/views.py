from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from core.mixins import CreatedByMixin
from .models import Entrega
from .serializers import EntregaSerializer


class EntregaListCreateView(CreatedByMixin, generics.ListCreateAPIView):
    queryset = Entrega.objects.select_related('cliente', 'creado_por').all()
    serializer_class   = EntregaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['cliente__nombre', 'estado', 'transportista']
    ordering_fields    = ['creado_en', 'estado', 'fecha_estimada']


class EntregaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Entrega.objects.select_related('cliente').all()
    serializer_class   = EntregaSerializer
    permission_classes = [IsAuthenticated]
