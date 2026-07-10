from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from core.permissions import IsAdminOrReadOnly
from core.mixins import AuditMixin
from .models import Producto
from .serializers import ProductoSerializer, ProductoMiniSerializer
import openpyxl
from decimal import Decimal


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

    def perform_update(self, serializer):
        producto_anterior = self.get_object()
        precio_venta_ant = producto_anterior.precio_venta
        precio_costo_ant = producto_anterior.precio_costo
        stock_ant = producto_anterior.stock

        producto_nuevo = serializer.save()

        from .models import AuditoriaProducto
        motivo = self.request.data.get('motivo_auditoria', 'Modificado desde panel administrativo')

        cambios = []
        if precio_venta_ant != producto_nuevo.precio_venta:
            cambios.append(('Precio Venta', str(precio_venta_ant), str(producto_nuevo.precio_venta)))
        if precio_costo_ant != producto_nuevo.precio_costo:
            cambios.append(('Precio Costo', str(precio_costo_ant), str(producto_nuevo.precio_costo)))
        if stock_ant != producto_nuevo.stock:
            cambios.append(('Stock', str(stock_ant), str(producto_nuevo.stock)))

        for campo, val_ant, val_nue in cambios:
            AuditoriaProducto.objects.create(
                producto=producto_nuevo,
                usuario=self.request.user,
                campo_modificado=campo,
                valor_anterior=val_ant,
                valor_nuevo=val_nue,
                motivo=motivo
            )

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

class ProductoImportView(APIView):
    """POST /api/productos/importar/"""
    permission_classes = [IsAdminOrReadOnly]
    
    @transaction.atomic
    def post(self, request):
        archivo = request.FILES.get('archivo')
        if not archivo:
            return Response({'error': 'No se proporcionó archivo'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            wb = openpyxl.load_workbook(archivo, data_only=True)
            sheet = wb.active
            creados = 0
            actualizados = 0
            
            for i, row in enumerate(sheet.iter_rows(values_only=True), 1):
                if i == 1: continue
                if not row[0]: continue
                
                codigo = str(row[0]).strip()
                nombre = str(row[1]).strip() if row[1] else ''
                categoria = str(row[2]).strip() if row[2] else 'General'
                precio_venta = row[3] or 0
                precio_costo = row[4] or 0
                stock_minimo = row[5] or 5
                
                if not nombre: continue
                
                prod, created = Producto.objects.update_or_create(
                    codigo=codigo,
                    defaults={
                        'nombre': nombre,
                        'categoria': categoria,
                        'precio_venta': Decimal(str(precio_venta)),
                        'precio_costo': Decimal(str(precio_costo)),
                        'stock_minimo': int(stock_minimo)
                    }
                )
                if created: creados += 1
                else: actualizados += 1
                
            from core.utils import log_action
            log_action(
                user=request.user, action='CREATE', modulo='Inventario',
                modelo='Producto', objeto_id=0,
                descripcion=f"Importación masiva: {creados} creados, {actualizados} actualizados.",
                request=request
            )
                
            return Response({'mensaje': f'Importación exitosa. Creados: {creados}, Actualizados: {actualizados}'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AuditoriaProductoListView(APIView):
    """
    GET /api/productos/<id>/auditoria/
    Devuelve el historial de cambios de precio y stock de un producto.
    """
    permission_classes = [IsAdminOrReadOnly]

    def get(self, request, pk):
        from .models import AuditoriaProducto
        auditorias = AuditoriaProducto.objects.filter(producto_id=pk).select_related('usuario')
        data = [
            {
                'id': a.id,
                'fecha': a.fecha,
                'usuario': a.usuario.nombre if a.usuario else 'Sistema',
                'campo_modificado': a.campo_modificado,
                'valor_anterior': a.valor_anterior,
                'valor_nuevo': a.valor_nuevo,
                'motivo': a.motivo,
            }
            for a in auditorias
        ]
        return Response(data)