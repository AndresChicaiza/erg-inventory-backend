from rest_framework import serializers
from .models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    documento_completo = serializers.ReadOnlyField()
    aplica_retefuente  = serializers.ReadOnlyField()
    aplica_reteiva     = serializers.ReadOnlyField()

    class Meta:
        model  = Cliente
        fields = '__all__'
        read_only_fields = ('id', 'creado_en', 'actualizado_en')


class ClienteMiniSerializer(serializers.ModelSerializer):
    """Serializer liviano para selectores."""
    class Meta:
        model  = Cliente
        # ✅ Fix: razon_social en lugar de nombre
        fields = ('id', 'razon_social', 'numero_documento', 'tipo_documento',
                  'email', 'telefono', 'regimen_tributario',
                  'gran_contribuyente', 'agente_retenedor')