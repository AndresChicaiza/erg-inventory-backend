from rest_framework import generics, filters
from core.permissions import IsAdminOrReadOnly
from .models import Producto
from .serializers import ProductoSerializer


class ProductoListCreateView(generics.ListCreateAPIView):
    queryset         = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ['nombre', 'codigo', 'categoria']
    ordering_fields  = ['nombre', 'stock', 'precio_venta', 'categoria']


class ProductoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset         = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminOrReadOnly]
