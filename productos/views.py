from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from core.permissions import IsAdminOrReadOnly
from core.mixins import AuditMixin
from .models import Producto
from .serializers import ProductoSerializer, ProductoMiniSerializer


class ProductoListCreateView(AuditMixin, generics.ListCreateAPIView):
    queryset           = Producto.objects.all()
    serializer_class   = ProductoSerializer
    permission_classes = [IsAdminOrReadOnly]
    audit_modulo       = 'Inventario'
    audit_modelo       = 'Producto'
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['nombre', 'codigo', 'categoria']
    ordering_fields    = ['nombre', 'stock', 'precio_venta', 'categoria']

    @transaction.atomic
    def perform_create(self, serializer):
        producto = serializer.save()

        # Si viene bodega_id, registrar el stock inicial en esa bodega
        bodega_id = self.request.data.get('bodega_id')
        if bodega_id and producto.stock > 0:
            from bodegas.models import StockBodega, Bodega
            try:
                bodega = Bodega.objects.get(id=bodega_id)
                StockBodega.objects.create(
                    bodega=bodega,
                    producto=producto,
                    cantidad=producto.stock
                )
            except Bodega.DoesNotExist:
                pass  # bodega_id inválido → se ignora silenciosamente
        
        from core.utils import log_action
        log_action(
            user=self.request.user, action='CREATE', modulo='Inventario',
            modelo='Producto', objeto_id=producto.id,
            descripcion=f"Creado producto: {producto.nombre} (Stock inicial: {producto.stock})",
            request=self.request
        )

class ProductoDetailView(AuditMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset           = Producto.objects.all()
    serializer_class   = ProductoSerializer
    permission_classes = [IsAdminOrReadOnly]
    audit_modulo       = 'Inventario'
    audit_modelo       = 'Producto'

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            from django.db.models import ProtectedError
            if isinstance(e, ProtectedError):
                return Response(
                    {"error": "No se puede eliminar el producto porque tiene ventas o movimientos asociados. Te sugerimos cambiar su estado a 'Inactivo'."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProductoStockBodegasView(APIView):
    """
    GET /api/productos/<id>/stock-bodegas/
    Devuelve el stock de un producto desglosado por bodega.
    Útil para mostrar en el selector de bodega al crear una venta.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from bodegas.models import StockBodega
        try:
            producto = Producto.objects.get(pk=pk)
        except Producto.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=404)

        stocks = StockBodega.objects.select_related('bodega').filter(
            producto=producto, cantidad__gt=0
        )
        data = [
            {
                'bodega_id':     s.bodega.id,
                'bodega_nombre': s.bodega.nombre,
                'bodega_codigo': s.bodega.codigo,
                'cantidad':      s.cantidad,
            }
            for s in stocks
        ]
        return Response({
            'producto_nombre': producto.nombre,
            'stock_total':     producto.stock,
            'bodegas':         data,
        })


class LoteListView(generics.ListAPIView):
    """
    GET /api/productos/<producto_id>/lotes/
    Devuelve los lotes activos (con stock disponible o en general) de un producto.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from .models import Lote
        producto_id = self.kwargs['pk']
        # Filtramos lotes que pertenezcan al producto.
        # Ordenamos por fecha de vencimiento más próxima.
        return Lote.objects.filter(producto_id=producto_id).order_by('fecha_vencimiento')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = [
            {
                'id': lote.id,
                'numero_lote': lote.numero_lote,
                'fecha_vencimiento': lote.fecha_vencimiento,
                'stock_disponible': lote.stock_disponible,
                'estado': lote.estado
            }
            for lote in queryset
        ]
        return Response(data)