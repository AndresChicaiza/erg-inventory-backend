from rest_framework import serializers
from .models import Entrega


class EntregaSerializer(serializers.ModelSerializer):
    cliente_nombre    = serializers.CharField(source='cliente.nombre',    read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.nombre', read_only=True)

    class Meta:
        model  = Entrega
        fields = '__all__'
        read_only_fields = ('id', 'creado_en', 'actualizado_en')
