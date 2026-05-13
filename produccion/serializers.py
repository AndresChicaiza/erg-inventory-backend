from rest_framework import serializers
from .models import Receta, IngredienteReceta, OrdenProduccion, ConsumoProduccion

class IngredienteRecetaSerializer(serializers.ModelSerializer):
    producto_materia_nombre = serializers.ReadOnlyField(source='producto_materia.nombre')
    producto_materia_unidad = serializers.ReadOnlyField(source='producto_materia.unidad_medida')
    precio_costo = serializers.ReadOnlyField(source='producto_materia.precio_costo')

    class Meta:
        model = IngredienteReceta
        fields = '__all__'
        read_only_fields = ['receta']


class RecetaSerializer(serializers.ModelSerializer):
    producto_terminado_nombre = serializers.ReadOnlyField(source='producto_terminado.nombre')
    ingredientes = IngredienteRecetaSerializer(many=True, read_only=True)
    
    class Meta:
        model = Receta
        fields = '__all__'


class ConsumoProduccionSerializer(serializers.ModelSerializer):
    producto_materia_nombre = serializers.ReadOnlyField(source='producto_materia.nombre')
    producto_materia_unidad = serializers.ReadOnlyField(source='producto_materia.unidad_medida')

    class Meta:
        model = ConsumoProduccion
        fields = '__all__'
        read_only_fields = ['orden']


class OrdenProduccionSerializer(serializers.ModelSerializer):
    producto_terminado_nombre = serializers.ReadOnlyField(source='receta.producto_terminado.nombre')
    creado_por_nombre = serializers.ReadOnlyField(source='creado_por.nombre')
    consumos = ConsumoProduccionSerializer(many=True, read_only=True)

    class Meta:
        model = OrdenProduccion
        fields = '__all__'
        read_only_fields = ['numero', 'creado_por', 'fecha_inicio', 'fecha_fin']
