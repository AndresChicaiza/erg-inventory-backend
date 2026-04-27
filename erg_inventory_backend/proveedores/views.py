from rest_framework import generics, filters
from core.permissions import IsAdminOrReadOnly
from .models import Proveedor
from .serializers import ProveedorSerializer

class ProveedorListCreateView(generics.ListCreateAPIView):
    queryset         = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ['empresa', 'contacto', 'ciudad', 'categoria']
    ordering_fields  = ['empresa', 'categoria', 'tipo']

class ProveedorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset         = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAdminOrReadOnly]
