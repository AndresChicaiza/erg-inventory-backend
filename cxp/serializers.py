from rest_framework import serializers
from .models import CuentaPorPagar, PagoCXP


class PagoCXPSerializer(serializers.ModelSerializer):
    creado_por_nombre = serializers.CharField(source='creado_por.nombre', read_only=True)

    class Meta:
        model  = PagoCXP
        fields = '__all__'
        read_only_fields = ('id', 'fecha', 'creado_en')


class CXPSerializer(serializers.ModelSerializer):
    # ✅ Fix: usa razon_social en lugar de empresa
    proveedor_nombre      = serializers.CharField(source='proveedor.razon_social',    read_only=True)
    proveedor_documento   = serializers.CharField(source='proveedor.numero_documento', read_only=True)
    proveedor_tipo_doc    = serializers.CharField(source='proveedor.tipo_documento',   read_only=True)
    # Datos bancarios para el modal de pago
    proveedor_banco       = serializers.CharField(source='proveedor.banco',            read_only=True)
    proveedor_tipo_cuenta = serializers.CharField(source='proveedor.tipo_cuenta',      read_only=True)
    proveedor_cuenta      = serializers.CharField(source='proveedor.cuenta_bancaria',  read_only=True)
    creado_por_nombre     = serializers.CharField(source='creado_por.nombre',          read_only=True)
    pagos                 = PagoCXPSerializer(many=True, read_only=True)
    dias_vencimiento      = serializers.ReadOnlyField()
    alerta_vencimiento    = serializers.ReadOnlyField()

    class Meta:
        model  = CuentaPorPagar
        fields = '__all__'
        read_only_fields = ('id', 'saldo', 'fecha_emision', 'creado_en', 'actualizado_en')