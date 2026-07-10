from rest_framework import serializers
from .models import CatalogoPublico, PedidoOnline, DetallePedidoOnline


# ─────────────────────────────────────────────────────────────────────────────
# Catálogo público (lectura para el portal B2B)
# ─────────────────────────────────────────────────────────────────────────────
class CatalogoPublicoSerializer(serializers.ModelSerializer):
    """Solo lectura — para el portal de clientes."""
    nombre          = serializers.CharField(source='producto.nombre')
    codigo          = serializers.CharField(source='producto.codigo')
    unidad_medida   = serializers.CharField(source='producto.unidad_medida')
    stock           = serializers.DecimalField(source='producto.stock', max_digits=14, decimal_places=3)
    precio          = serializers.DecimalField(source='precio_efectivo', max_digits=14, decimal_places=2)
    descripcion     = serializers.CharField(source='descripcion_efectiva')
    categoria       = serializers.CharField(source='categoria_efectiva')
    imagen_url      = serializers.SerializerMethodField()

    class Meta:
        model  = CatalogoPublico
        fields = [
            'id', 'nombre', 'codigo', 'unidad_medida', 'stock',
            'precio', 'descripcion', 'categoria', 'imagen_url',
            'stock_maximo_pedido', 'orden',
        ]

    def get_imagen_url(self, obj):
        request = self.context.get('request')
        img = obj.imagen_efectiva
        if img and hasattr(img, 'url'):
            return request.build_absolute_uri(img.url) if request else img.url
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Admin — gestión del catálogo desde el ERP
# ─────────────────────────────────────────────────────────────────────────────
class CatalogoAdminSerializer(serializers.ModelSerializer):
    nombre_producto  = serializers.CharField(source='producto.nombre', read_only=True)
    codigo_producto  = serializers.CharField(source='producto.codigo', read_only=True)
    stock_erp        = serializers.DecimalField(source='producto.stock', max_digits=14, decimal_places=3, read_only=True)
    precio_venta_erp = serializers.DecimalField(source='producto.precio_venta', max_digits=14, decimal_places=2, read_only=True)
    imagen_url       = serializers.SerializerMethodField()

    class Meta:
        model  = CatalogoPublico
        fields = [
            'id', 'producto', 'nombre_producto', 'codigo_producto',
            'visible', 'descripcion_publica', 'precio_publico',
            'imagen_publica', 'imagen_url', 'categoria_display',
            'stock_maximo_pedido', 'orden',
            'stock_erp', 'precio_venta_erp',
            'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['creado_en', 'actualizado_en']

    def get_imagen_url(self, obj):
        request = self.context.get('request')
        img = obj.imagen_efectiva
        if img and hasattr(img, 'url'):
            return request.build_absolute_uri(img.url) if request else img.url
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Detalle del pedido
# ─────────────────────────────────────────────────────────────────────────────
class DetallePedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = DetallePedidoOnline
        fields = [
            'id', 'catalogo_item', 'producto', 'nombre_producto',
            'cantidad', 'precio_unitario', 'subtotal_linea',
        ]
        read_only_fields = ['subtotal_linea', 'producto', 'nombre_producto']


class DetallePedidoCreateSerializer(serializers.Serializer):
    """Para recibir los ítems al crear el pedido."""
    catalogo_item_id = serializers.IntegerField()
    cantidad         = serializers.DecimalField(max_digits=12, decimal_places=3, min_value=0.001)


# ─────────────────────────────────────────────────────────────────────────────
# Pedido Online
# ─────────────────────────────────────────────────────────────────────────────
class PedidoCreateSerializer(serializers.ModelSerializer):
    """Para que el portal cree un nuevo pedido."""
    detalles = DetallePedidoCreateSerializer(many=True, write_only=True)

    class Meta:
        model  = PedidoOnline
        fields = [
            'cliente_nit', 'cliente_nombre', 'cliente_email',
            'cliente_telefono', 'cliente_ciudad', 'cliente_direccion',
            'notas', 'detalles',
        ]

    def validate_detalles(self, value):
        if not value:
            raise serializers.ValidationError('Debe incluir al menos un producto.')
        return value

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles')
        pedido = PedidoOnline.objects.create(**validated_data)

        for item in detalles_data:
            cat_item = CatalogoPublico.objects.select_related('producto').get(
                pk=item['catalogo_item_id'], visible=True
            )
            DetallePedidoOnline.objects.create(
                pedido=pedido,
                catalogo_item=cat_item,
                producto=cat_item.producto,
                nombre_producto=cat_item.producto.nombre,
                cantidad=item['cantidad'],
                precio_unitario=cat_item.precio_efectivo,
            )

        pedido.recalcular_totales()

        # Vincular con cliente ERP si existe por NIT
        if pedido.cliente_nit:
            from clientes.models import Cliente
            cliente_erp = Cliente.objects.filter(
                numero_documento=pedido.cliente_nit
            ).first()
            if cliente_erp:
                pedido.cliente_erp = cliente_erp
                pedido.save(update_fields=['cliente_erp'])

        return pedido


class PedidoAdminSerializer(serializers.ModelSerializer):
    """Serializer completo para el admin del ERP."""
    detalles             = DetallePedidoSerializer(many=True, read_only=True)
    cliente_erp_nombre   = serializers.CharField(source='cliente_erp.razon_social', read_only=True, default=None)
    factura_numero       = serializers.CharField(source='factura.numero_completo', read_only=True, default=None)
    revisado_por_nombre  = serializers.CharField(source='revisado_por.nombre', read_only=True, default=None)

    class Meta:
        model  = PedidoOnline
        fields = [
            'id', 'token',
            'cliente_nit', 'cliente_nombre', 'cliente_email',
            'cliente_telefono', 'cliente_ciudad', 'cliente_direccion',
            'notas', 'motivo_rechazo',
            'subtotal', 'total', 'estado',
            'cliente_erp', 'cliente_erp_nombre',
            'factura', 'factura_numero',
            'revisado_por', 'revisado_por_nombre', 'revisado_en',
            'creado_en', 'actualizado_en',
            'detalles',
        ]
        read_only_fields = [
            'token', 'subtotal', 'total',
            'creado_en', 'actualizado_en',
            'revisado_por', 'revisado_en',
        ]


class PedidoStatusSerializer(serializers.ModelSerializer):
    """Solo para consulta pública por token."""
    detalles = DetallePedidoSerializer(many=True, read_only=True)

    class Meta:
        model  = PedidoOnline
        fields = [
            'token', 'cliente_nombre', 'estado',
            'subtotal', 'total',
            'motivo_rechazo', 'creado_en',
            'detalles',
        ]


class ResumenMarketplaceSerializer(serializers.Serializer):
    """KPIs del marketplace para el dashboard del ERP."""
    total_pedidos       = serializers.IntegerField()
    pedidos_pendientes  = serializers.IntegerField()
    pedidos_aprobados   = serializers.IntegerField()
    pedidos_rechazados  = serializers.IntegerField()
    valor_total_aprobado = serializers.DecimalField(max_digits=16, decimal_places=2)
    productos_visibles  = serializers.IntegerField()
