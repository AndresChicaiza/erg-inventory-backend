from rest_framework import serializers
from .models import PeriodoNomina, LineaNomina, ConceptoNomina


class ConceptoNominaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ConceptoNomina
        fields = '__all__'


class LineaNominaSerializer(serializers.ModelSerializer):
    empleado_nombre = serializers.CharField(source='empleado.nombre', read_only=True)
    empleado_email  = serializers.CharField(source='empleado.email',  read_only=True)

    class Meta:
        model  = LineaNomina
        fields = '__all__'
        read_only_fields = ('total_devengado', 'salud', 'pension', 'total_deducciones', 'neto_pagar')


class PeriodoNominaSerializer(serializers.ModelSerializer):
    lineas             = LineaNominaSerializer(many=True, read_only=True)
    creado_por_nombre  = serializers.CharField(source='creado_por.nombre', read_only=True)

    class Meta:
        model  = PeriodoNomina
        fields = '__all__'
        read_only_fields = ('id', 'total_devengado', 'total_deducciones', 'total_neto', 'creado_en', 'actualizado_en')
