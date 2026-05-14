from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminOrReadOnly, ADMIN_CONTA_VEND_BOD_JEFE, _rol
from rest_framework.permissions import BasePermission
from .models import Proveedor
from .serializers import ProveedorSerializer

class CanWriteProveedor(BasePermission):
    """Lectura para todos; escritura para Admin, Contador, Bodeguero, JefeFabrica."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated): return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'): return True
        return _rol(request, *ADMIN_CONTA_VEND_BOD_JEFE)

class ProveedorListCreateView(generics.ListCreateAPIView):
    queryset         = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [CanWriteProveedor]
    filter_backends  = [filters.SearchFilter, filters.OrderingFilter]
    search_fields    = ['empresa', 'contacto', 'ciudad', 'categoria']
    ordering_fields  = ['empresa', 'categoria', 'tipo']

class ProveedorDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset         = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [CanWriteProveedor]
