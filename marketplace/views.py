from django.utils import timezone
from django.db.models import Sum, Q
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import CatalogoPublico, PedidoOnline, DetallePedidoOnline
from .serializers import (
    CatalogoPublicoSerializer,
    CatalogoAdminSerializer,
    PedidoCreateSerializer,
    PedidoAdminSerializer,
    PedidoStatusSerializer,
)
from core.permissions import CanCreateVenta


# ═════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS PÚBLICOS — sin autenticación (portal B2B)
# ═════════════════════════════════════════════════════════════════════════════

class CatalogoPublicoListView(generics.ListAPIView):
    """
    GET /api/marketplace/catalogo/
    Retorna todos los productos visibles en el portal B2B.
    No requiere autenticación.
    """
    serializer_class   = CatalogoPublicoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = CatalogoPublico.objects.filter(
            visible=True
        ).select_related('producto').order_by('orden', 'producto__nombre')

        # Filtro por categoría
        categoria = self.request.query_params.get('categoria')
        if categoria:
            qs = qs.filter(
                Q(categoria_display__icontains=categoria) |
                Q(producto__categoria__icontains=categoria)
            )

        # Búsqueda por nombre
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(
                Q(producto__nombre__icontains=q) |
                Q(producto__codigo__icontains=q) |
                Q(descripcion_publica__icontains=q)
            )

        return qs

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True, context={'request': request})

        # Extraer categorías únicas para filtros del portal
        categorias = list({
            item.categoria_efectiva
            for item in qs
            if item.categoria_efectiva
        })
        categorias.sort()

        return Response({
            'count':      qs.count(),
            'categorias': categorias,
            'productos':  serializer.data,
        })


class PedidoCreateView(generics.CreateAPIView):
    """
    POST /api/marketplace/pedidos/
    El cliente del portal crea un pedido. No requiere autenticación.
    """
    serializer_class   = PedidoCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pedido = serializer.save()
        return Response({
            'mensaje': '¡Pedido recibido! Te contactaremos pronto.',
            'pedido_id': pedido.pk,
            'token':     pedido.token,
            'total':     str(pedido.total),
            'estado':    pedido.estado,
        }, status=status.HTTP_201_CREATED)


class PedidoStatusView(APIView):
    """
    GET /api/marketplace/pedidos/estado/<token>/
    El cliente consulta el estado de su pedido con el token. Sin login.
    """
    permission_classes = [AllowAny]

    def get(self, request, token):
        try:
            pedido = PedidoOnline.objects.prefetch_related('detalles').get(token=token)
        except PedidoOnline.DoesNotExist:
            return Response({'detail': 'Pedido no encontrado.'}, status=404)

        return Response(PedidoStatusSerializer(pedido).data)


# ═════════════════════════════════════════════════════════════════════════════
#  ENDPOINTS ADMIN — requieren autenticación (panel ERP)
# ═════════════════════════════════════════════════════════════════════════════

class PedidoAdminListView(generics.ListAPIView):
    """
    GET /api/marketplace/admin/pedidos/
    Lista todos los pedidos para el equipo de ventas.
    Filtros: estado, fecha_desde, fecha_hasta, q (nombre/email/nit)
    """
    serializer_class   = PedidoAdminSerializer
    permission_classes = [IsAuthenticated, CanCreateVenta]

    def get_queryset(self):
        qs = PedidoOnline.objects.select_related(
            'cliente_erp', 'factura', 'revisado_por'
        ).prefetch_related('detalles__catalogo_item').order_by('-creado_en')

        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(
                Q(cliente_nombre__icontains=q) |
                Q(cliente_email__icontains=q) |
                Q(cliente_nit__icontains=q)
            )

        fecha_desde = self.request.query_params.get('fecha_desde')
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_desde:
            qs = qs.filter(creado_en__date__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(creado_en__date__lte=fecha_hasta)

        return qs


class PedidoAdminDetailView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/marketplace/admin/pedidos/<id>/
    PATCH /api/marketplace/admin/pedidos/<id>/
    """
    serializer_class   = PedidoAdminSerializer
    permission_classes = [IsAuthenticated, CanCreateVenta]
    queryset           = PedidoOnline.objects.select_related(
        'cliente_erp', 'factura', 'revisado_por'
    ).prefetch_related('detalles')


class PedidoAprobarView(APIView):
    """
    POST /api/marketplace/admin/pedidos/<id>/aprobar/
    Aprueba el pedido y genera automáticamente una Factura en estado 'Borrador'.
    """
    permission_classes = [IsAuthenticated, CanCreateVenta]

    def post(self, request, pk):
        try:
            pedido = PedidoOnline.objects.prefetch_related('detalles__producto').get(pk=pk)
        except PedidoOnline.DoesNotExist:
            return Response({'detail': 'Pedido no encontrado.'}, status=404)

        if pedido.estado not in ('Pendiente', 'En_Revision'):
            return Response(
                {'detail': f'No se puede aprobar un pedido en estado "{pedido.estado}".'},
                status=400
            )

        # Buscar o crear cliente en el ERP
        cliente_erp = pedido.cliente_erp
        if not cliente_erp and pedido.cliente_nit:
            from clientes.models import Cliente
            cliente_erp = Cliente.objects.filter(numero_documento=pedido.cliente_nit).first()

        if not cliente_erp:
            return Response(
                {'detail': 'El cliente no existe en el ERP. Créalo primero en el módulo de Clientes.'},
                status=400
            )

        # Crear factura en borrador
        from facturacion.models import Factura, DetalleFactura
        factura = Factura.objects.create(
            cliente=cliente_erp,
            vendedor=request.user,
            condicion_pago='Contado',
            medio_pago='Efectivo',
            estado='Borrador',
            notas=f'Generada desde Pedido Online #{pedido.pk}. {pedido.notas}',
            creado_por=request.user,
        )

        for detalle in pedido.detalles.all():
            if detalle.producto:
                DetalleFactura.objects.create(
                    factura=factura,
                    producto=detalle.producto,
                    descripcion=detalle.nombre_producto,
                    cantidad=detalle.cantidad,
                    precio_unitario=detalle.precio_unitario,
                    iva_tipo=detalle.producto.iva_tipo,
                )

        factura.recalcular_totales()

        # Actualizar pedido
        pedido.estado        = 'Aprobado'
        pedido.factura       = factura
        pedido.cliente_erp   = cliente_erp
        pedido.revisado_por  = request.user
        pedido.revisado_en   = timezone.now()
        pedido.save()

        return Response({
            'mensaje':   'Pedido aprobado. Factura en borrador creada.',
            'factura_id': factura.pk,
            'factura_numero': factura.numero_completo,
        })


class PedidoRechazarView(APIView):
    """
    POST /api/marketplace/admin/pedidos/<id>/rechazar/
    Body: { "motivo": "..." }
    """
    permission_classes = [IsAuthenticated, CanCreateVenta]

    def post(self, request, pk):
        try:
            pedido = PedidoOnline.objects.get(pk=pk)
        except PedidoOnline.DoesNotExist:
            return Response({'detail': 'Pedido no encontrado.'}, status=404)

        if pedido.estado == 'Aprobado':
            return Response({'detail': 'No se puede rechazar un pedido ya aprobado.'}, status=400)

        motivo = request.data.get('motivo', '').strip()
        pedido.estado         = 'Rechazado'
        pedido.motivo_rechazo = motivo
        pedido.revisado_por   = request.user
        pedido.revisado_en    = timezone.now()
        pedido.save()

        return Response({'mensaje': 'Pedido rechazado correctamente.'})


# ─── Catálogo — gestión admin ────────────────────────────────────────────────

class CatalogoAdminListView(generics.ListCreateAPIView):
    """
    GET  /api/marketplace/admin/catalogo/      — Lista con filtros
    POST /api/marketplace/admin/catalogo/      — Crear ítem (exponer un producto)
    """
    permission_classes = [IsAuthenticated, CanCreateVenta]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        return CatalogoAdminSerializer

    def get_queryset(self):
        qs = CatalogoPublico.objects.select_related('producto').order_by('orden', 'producto__nombre')
        solo_visibles = self.request.query_params.get('solo_visibles')
        if solo_visibles == 'true':
            qs = qs.filter(visible=True)
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(
                Q(producto__nombre__icontains=q) |
                Q(producto__codigo__icontains=q)
            )
        return qs


class CatalogoAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/marketplace/admin/catalogo/<id>/
    PATCH  /api/marketplace/admin/catalogo/<id>/
    DELETE /api/marketplace/admin/catalogo/<id>/
    """
    serializer_class   = CatalogoAdminSerializer
    permission_classes = [IsAuthenticated, CanCreateVenta]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]
    queryset           = CatalogoPublico.objects.select_related('producto')


class ToggleVisibilidadView(APIView):
    """
    POST /api/marketplace/admin/catalogo/<id>/toggle/
    Cambia el estado visible/oculto de un ítem del catálogo.
    """
    permission_classes = [IsAuthenticated, CanCreateVenta]

    def post(self, request, pk):
        try:
            item = CatalogoPublico.objects.get(pk=pk)
        except CatalogoPublico.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=404)

        item.visible = not item.visible
        item.save(update_fields=['visible'])
        return Response({
            'id':      item.pk,
            'visible': item.visible,
            'mensaje': 'Publicado en catálogo.' if item.visible else 'Ocultado del catálogo.',
        })


class ResumenMarketplaceView(APIView):
    """
    GET /api/marketplace/admin/resumen/
    KPIs del marketplace para el dashboard del ERP.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pedidos = PedidoOnline.objects.all()
        aprobados = pedidos.filter(estado='Aprobado')
        return Response({
            'total_pedidos':         pedidos.count(),
            'pedidos_pendientes':    pedidos.filter(estado__in=['Pendiente', 'En_Revision']).count(),
            'pedidos_aprobados':     aprobados.count(),
            'pedidos_rechazados':    pedidos.filter(estado='Rechazado').count(),
            'valor_total_aprobado':  aprobados.aggregate(v=Sum('total'))['v'] or 0,
            'productos_visibles':    CatalogoPublico.objects.filter(visible=True).count(),
        })
