from rest_framework import serializers
from .models import ConfiguracionEmpresa, TarifaReteICA, TarifaRetefuente


class ConfiguracionEmpresaSerializer(serializers.ModelSerializer):
    nit_completo             = serializers.ReadOnlyField()
    numero_factura_siguiente = serializers.SerializerMethodField()

    class Meta:
        model  = ConfiguracionEmpresa
        fields = '__all__'
        read_only_fields = ('consecutivo_actual', 'actualizado_en')

    def get_numero_factura_siguiente(self, obj):
        return obj.numero_factura_formateado(obj.consecutivo_actual)


class TarifaReteICASerializer(serializers.ModelSerializer):
    class Meta:
        model  = TarifaReteICA
        fields = '__all__'


class TarifaRetefuenteSerializer(serializers.ModelSerializer):
    concepto_display = serializers.CharField(source='get_concepto_display', read_only=True)

    class Meta:
        model  = TarifaRetefuente
        fields = '__all__'