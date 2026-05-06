from rest_framework import serializers
from .models import CuentaPorCobrar, PagoCXC


class PagoCXCSerializer(serializers.ModelSerializer):
    creado_por_nombre = serializers.CharField(source='creado_por.nombre', read_only=True)

    class Meta:
        model  = PagoCXC
        fields = '__all__'
        read_only_fields = ('id', 'fecha', 'creado_en')


class CXCSerializer(serializers.ModelSerializer):
    # ✅ Fix: usa razon_social en lugar de nombre
    cliente_nombre      = serializers.CharField(source='cliente.razon_social',    read_only=True)
    cliente_documento   = serializers.CharField(source='cliente.numero_documento', read_only=True)
    cliente_tipo_doc    = serializers.CharField(source='cliente.tipo_documento',   read_only=True)
    creado_por_nombre   = serializers.CharField(source='creado_por.nombre',        read_only=True)
    pagos               = PagoCXCSerializer(many=True, read_only=True)
    dias_vencimiento    = serializers.ReadOnlyField()
    alerta_vencimiento  = serializers.ReadOnlyField()

    class Meta:
        model  = CuentaPorCobrar
        fields = '__all__'
        read_only_fields = ('id', 'saldo', 'fecha_emision', 'creado_en', 'actualizado_en')