from rest_framework import serializers
from .models import Factura, DetalleFactura, NotaCredito, DetalleNotaCredito


class DetalleFacturaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)

    class Meta:
        model  = DetalleFactura
        fields = '__all__'
        read_only_fields = ('id', 'valor_descuento', 'subtotal_linea',
                            'valor_iva_linea', 'total_linea')


class FacturaSerializer(serializers.ModelSerializer):
    cliente_razon_social   = serializers.CharField(source='cliente.razon_social',     read_only=True)
    cliente_documento      = serializers.CharField(source='cliente.numero_documento',  read_only=True)
    cliente_tipo_doc       = serializers.CharField(source='cliente.tipo_documento',    read_only=True)
    cliente_dv             = serializers.CharField(source='cliente.digito_verificacion', read_only=True)
    cliente_direccion      = serializers.CharField(source='cliente.direccion',         read_only=True)
    cliente_ciudad         = serializers.CharField(source='cliente.ciudad',            read_only=True)
    cliente_email          = serializers.CharField(source='cliente.email',             read_only=True)
    cliente_telefono       = serializers.CharField(source='cliente.telefono',          read_only=True)
    cliente_regimen        = serializers.CharField(source='cliente.regimen_tributario',read_only=True)
    cliente_agente_ret     = serializers.BooleanField(source='cliente.agente_retenedor', read_only=True)
    cliente_gran_contrib   = serializers.BooleanField(source='cliente.gran_contribuyente', read_only=True)
    creado_por_nombre      = serializers.CharField(source='creado_por.nombre',         read_only=True)
    vendedor_nombre        = serializers.CharField(source='vendedor.nombre',           read_only=True)
    bodega_nombre          = serializers.CharField(source='bodega.nombre',             read_only=True)
    detalles               = DetalleFacturaSerializer(many=True, read_only=True)

    class Meta:
        model  = Factura
        fields = '__all__'
        read_only_fields = (
            'id', 'numero', 'prefijo', 'numero_completo',
            'subtotal', 'descuento_total',
            'base_iva_0', 'base_iva_5', 'base_iva_19', 'base_excluida',
            'valor_iva_5', 'valor_iva_19', 'valor_iva_total',
            'retefuente_pct', 'valor_retefuente',
            'reteiva_pct', 'valor_reteiva',
            'reteica_pct', 'valor_reteica',
            'total_retenciones', 'total_a_pagar',
            'cufe', 'qr_url', 'creado_en', 'actualizado_en',
        )


class FacturaListSerializer(serializers.ModelSerializer):
    """Serializer liviano para la lista — sin detalles."""
    cliente_razon_social = serializers.CharField(source='cliente.razon_social', read_only=True)
    cliente_documento    = serializers.CharField(source='cliente.numero_documento', read_only=True)

    class Meta:
        model  = Factura
        fields = (
            'id', 'numero_completo', 'fecha_emision', 'fecha_vencimiento',
            'cliente', 'cliente_razon_social', 'cliente_documento',
            'condicion_pago', 'medio_pago', 'estado', 'requiere_envio',
            'subtotal', 'valor_iva_total', 'total_retenciones', 'total_a_pagar',
            'cufe', 'qr_url',
        )


class CalcularImpuestosSerializer(serializers.Serializer):
    """Para el endpoint de cálculo previo sin guardar."""
    cliente_id          = serializers.IntegerField()
    concepto_retefuente = serializers.CharField(default='COMPRAS')
    items               = serializers.ListField(child=serializers.DictField())


class DetalleNotaCreditoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleNotaCredito
        fields = '__all__'
        read_only_fields = ('id', 'nota_credito', 'subtotal_linea', 'valor_iva_linea', 'total_linea')


class NotaCreditoSerializer(serializers.ModelSerializer):
    factura_numero = serializers.CharField(
        source='factura_original.numero_completo', read_only=True
    )
    detalles = DetalleNotaCreditoSerializer(many=True, required=False)

    class Meta:
        model  = NotaCredito
        fields = '__all__'
        read_only_fields = ('id', 'numero', 'numero_completo', 'creado_en', 'subtotal', 'valor_iva', 'total')

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles', [])
        nota_credito = NotaCredito.objects.create(**validated_data)
        
        for detalle_data in detalles_data:
            DetalleNotaCredito.objects.create(nota_credito=nota_credito, **detalle_data)
            
        nota_credito.recalcular_totales()
        return nota_credito