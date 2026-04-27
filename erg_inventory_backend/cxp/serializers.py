from rest_framework import serializers
from .models import CuentaPorPagar, PagoCXP


class PagoCXPSerializer(serializers.ModelSerializer):
    creado_por_nombre = serializers.CharField(source='creado_por.nombre', read_only=True)
    class Meta:
        model  = PagoCXP
        fields = '__all__'
        read_only_fields = ('id', 'fecha', 'creado_en')


class CXPSerializer(serializers.ModelSerializer):
    proveedor_nombre  = serializers.CharField(source='proveedor.empresa',  read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.nombre',  read_only=True)
    pagos             = PagoCXPSerializer(many=True, read_only=True)

    class Meta:
        model  = CuentaPorPagar
        fields = '__all__'
        read_only_fields = ('id', 'saldo', 'fecha_emision', 'creado_en', 'actualizado_en')
