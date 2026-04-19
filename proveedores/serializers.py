from rest_framework import serializers
from .models import Proveedor

class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Proveedor
        fields = '__all__'
        read_only_fields = ('id', 'creado_en', 'actualizado_en')

class ProveedorMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Proveedor
        fields = ('id', 'empresa', 'contacto', 'email')
