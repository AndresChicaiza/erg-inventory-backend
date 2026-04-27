from rest_framework import serializers
from .models import Bodega, StockBodega


class BodegaSerializer(serializers.ModelSerializer):
    responsable_nombre = serializers.CharField(source='responsable.nombre', read_only=True)
    total_productos    = serializers.SerializerMethodField()

    class Meta:
        model  = Bodega
        fields = '__all__'
        read_only_fields = ('id', 'creado_en', 'actualizado_en')

    def get_total_productos(self, obj):
        return obj.stocks.filter(cantidad__gt=0).count()


class StockBodegaSerializer(serializers.ModelSerializer):
    bodega_nombre   = serializers.CharField(source='bodega.nombre',   read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)

    class Meta:
        model  = StockBodega
        fields = '__all__'
        read_only_fields = ('id', 'actualizado_en')


class TransferenciaSerializer(serializers.Serializer):
    """Para transferir stock entre bodegas."""
    bodega_origen  = serializers.IntegerField()
    bodega_destino = serializers.IntegerField()
    producto       = serializers.IntegerField()
    cantidad       = serializers.IntegerField(min_value=1)
