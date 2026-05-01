from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from core.permissions import IsAdminOrReadOnly
from .models import Producto
from .serializers import ProductoSerializer, ProductoMiniSerializer


class ProductoListCreateView(generics.ListCreateAPIView):
    queryset           = Producto.objects.all()
    serializer_class   = ProductoSerializer
    permission_classes = [IsAdminOrReadOnly]
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


class ProductoDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Producto.objects.all()
    serializer_class   = ProductoSerializer
    permission_classes = [IsAdminOrReadOnly]

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
            'producto_id':     producto.id,
            'producto_nombre': producto.nombre,
            'stock_total':     producto.stock,
            'bodegas':         data,
        })