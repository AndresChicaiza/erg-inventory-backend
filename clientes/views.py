from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminOrReadOnly
from .models import Cliente
from .serializers import ClienteSerializer


class ClienteListCreateView(generics.ListCreateAPIView):
    queryset           = Cliente.objects.all()
    serializer_class   = ClienteSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    # ✅ Fix: campos correctos del modelo nuevo
    search_fields      = ['razon_social', 'numero_documento', 'email', 'ciudad', 'nombre_comercial']
    ordering_fields    = ['razon_social', 'tipo_documento', 'estado', 'ciudad']

    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)


class ClienteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Cliente.objects.all()
    serializer_class   = ClienteSerializer
    permission_classes = [IsAdminOrReadOnly]