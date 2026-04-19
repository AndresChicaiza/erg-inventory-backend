from rest_framework import serializers
from .models import Producto


class ProductoSerializer(serializers.ModelSerializer):
    estado_stock = serializers.ReadOnlyField()

    class Meta:
        model  = Producto
        fields = '__all__'
        read_only_fields = ('id', 'creado_en', 'actualizado_en')


class ProductoMiniSerializer(serializers.ModelSerializer):
    """Versión compacta para usar en relaciones."""
    class Meta:
        model  = Producto
        fields = ('id', 'codigo', 'nombre', 'precio_venta', 'precio_costo', 'stock')
