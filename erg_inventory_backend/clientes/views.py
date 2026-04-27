from rest_framework import generics, filters
from core.permissions import IsAdminOrReadOnly
from .models import Cliente
from .serializers import ClienteSerializer

class ClienteListCreateView(generics.ListCreateAPIView):
    queryset         = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ['nombre', 'email', 'ciudad', 'tipo']
    ordering_fields  = ['nombre', 'tipo', 'estado']

class ClienteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset         = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAdminOrReadOnly]
