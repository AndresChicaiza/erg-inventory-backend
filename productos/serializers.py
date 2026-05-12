from rest_framework import serializers
from .models import Producto


class ProductoSerializer(serializers.ModelSerializer):
    estado_stock      = serializers.ReadOnlyField()
    precio_sin_iva    = serializers.ReadOnlyField()
    valor_iva_unitario= serializers.ReadOnlyField()

    class Meta:
        model  = Producto
        fields = '__all__'
        read_only_fields = ('id', 'creado_en', 'actualizado_en')


class ProductoMiniSerializer(serializers.ModelSerializer):
    """Serializer liviano para selectores en factura."""
    precio_sin_iva    = serializers.ReadOnlyField()
    valor_iva_unitario= serializers.ReadOnlyField()

    class Meta:
        model  = Producto
        fields = (
            'id', 'codigo', 'nombre', 'categoria',
            'precio_venta', 'precio_sin_iva', 'valor_iva_unitario',
            'iva_tipo', 'iva_incluido', 'unidad_medida',
            'stock', 'estado',
        )