from rest_framework import serializers
from .models import Compra


class CompraSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source='proveedor.empresa',  read_only=True)
    producto_nombre  = serializers.CharField(source='producto.nombre',    read_only=True)
    producto_codigo  = serializers.CharField(source='producto.codigo',    read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.nombre', read_only=True)

    class Meta:
        model  = Compra
        fields = '__all__'
        read_only_fields = ('id', 'total', 'fecha', 'creado_en', 'actualizado_en')
