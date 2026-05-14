from rest_framework import serializers
from .models import Entrega, DetalleEntrega


class DetalleEntregaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)

    class Meta:
        model  = DetalleEntrega
        fields = '__all__'
        read_only_fields = ('id',)


class EntregaSerializer(serializers.ModelSerializer):
    cliente_nombre    = serializers.CharField(source='cliente.nombre',    read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.nombre', read_only=True)
    bodega_origen_nombre = serializers.CharField(source='bodega_origen.nombre', read_only=True)
    bodega_destino_nombre = serializers.CharField(source='bodega_destino.nombre', read_only=True)
    detalles          = DetalleEntregaSerializer(many=True, read_only=True)

    class Meta:
        model  = Entrega
        fields = '__all__'
        read_only_fields = ('id', 'creado_en', 'actualizado_en')
