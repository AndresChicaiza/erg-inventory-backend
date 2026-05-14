from rest_framework import serializers
from .models import Movimiento


class MovimientoSerializer(serializers.ModelSerializer):
    producto_nombre   = serializers.CharField(source='producto.nombre',     read_only=True)
    producto_codigo   = serializers.CharField(source='producto.codigo',     read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.nombre',   read_only=True)
    lote_nombre       = serializers.CharField(source='lote.numero_lote',    read_only=True)
    numero_lote       = serializers.CharField(write_only=True, required=False)
    fecha_vencimiento = serializers.DateField(write_only=True, required=False)

    class Meta:
        model  = Movimiento
        fields = '__all__'
        read_only_fields = ('id', 'fecha', 'creado_en')
