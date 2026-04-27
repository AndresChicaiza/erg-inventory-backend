from rest_framework import serializers
from .models import CuentaPorCobrar, PagoCXC


class PagoCXCSerializer(serializers.ModelSerializer):
    creado_por_nombre = serializers.CharField(source='creado_por.nombre', read_only=True)
    class Meta:
        model  = PagoCXC
        fields = '__all__'
        read_only_fields = ('id', 'fecha', 'creado_en')


class CXCSerializer(serializers.ModelSerializer):
    cliente_nombre    = serializers.CharField(source='cliente.nombre',    read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.nombre', read_only=True)
    pagos             = PagoCXCSerializer(many=True, read_only=True)

    class Meta:
        model  = CuentaPorCobrar
        fields = '__all__'
        read_only_fields = ('id', 'saldo', 'fecha_emision', 'creado_en', 'actualizado_en')
