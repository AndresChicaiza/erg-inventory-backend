from rest_framework import serializers
from .models import Empleado, PeriodoNomina, LineaNomina, ConceptoNomina


class EmpleadoSerializer(serializers.ModelSerializer):
    sede_nombre = serializers.CharField(source='sede.nombre', read_only=True)
    antiguedad  = serializers.FloatField(source='antiguedad_anios', read_only=True)

    class Meta:
        model  = Empleado
        fields = '__all__'
        read_only_fields = ('id', 'creado_en', 'actualizado_en')


class EmpleadoMiniSerializer(serializers.ModelSerializer):
    """Serializer ligero para listas desplegables."""
    class Meta:
        model  = Empleado
        fields = ('id', 'nombre', 'numero_documento', 'cargo', 'salario_base', 'estado')


class ConceptoNominaSerializer(serializers.ModelSerializer):
    class Meta:
        model  = ConceptoNomina
        fields = '__all__'


class LineaNominaSerializer(serializers.ModelSerializer):
    empleado_nombre   = serializers.CharField(source='empleado.nombre',           read_only=True)
    empleado_doc      = serializers.CharField(source='empleado.numero_documento',  read_only=True)
    empleado_cargo    = serializers.CharField(source='empleado.cargo',             read_only=True)
    empleado_banco    = serializers.CharField(source='empleado.banco',             read_only=True)
    empleado_cuenta   = serializers.CharField(source='empleado.numero_cuenta',     read_only=True)
    empleado_tipo_cta = serializers.CharField(source='empleado.tipo_cuenta',       read_only=True)

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
