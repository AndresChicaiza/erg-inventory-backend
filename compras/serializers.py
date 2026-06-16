from rest_framework import serializers
from .models import Compra, DetalleCompra, NotaCreditoProveedor, DetalleNotaCreditoProveedor
from django.db import transaction

class DetalleCompraSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)

    class Meta:
        model  = DetalleCompra
        fields = ('id', 'producto', 'producto_nombre', 'producto_codigo', 'cantidad', 'precio_unitario', 'porcentaje_iva', 'valor_iva', 'subtotal')
        read_only_fields = ('id', 'subtotal', 'valor_iva')


class CompraSerializer(serializers.ModelSerializer):
    proveedor_nombre      = serializers.CharField(source='proveedor.razon_social', read_only=True)
    proveedor_nit         = serializers.CharField(source='proveedor.numero_documento', read_only=True)
    proveedor_dv          = serializers.CharField(source='proveedor.digito_verificacion', read_only=True)
    proveedor_email       = serializers.CharField(source='proveedor.email', read_only=True)
    bodega_destino_nombre = serializers.CharField(source='bodega_destino.nombre', read_only=True)
    creado_por_nombre     = serializers.CharField(source='creado_por.nombre', read_only=True)
    detalles = DetalleCompraSerializer(many=True)

    class Meta:
        model  = Compra
        fields = '__all__'
        read_only_fields = ('id', 'subtotal', 'total_iva', 'total', 'fecha', 'fecha_vencimiento_pago', 'creado_en', 'actualizado_en')

    @transaction.atomic
    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles', [])
        compra = Compra.objects.create(**validated_data)
        
        for detalle_data in detalles_data:
            DetalleCompra.objects.create(compra=compra, **detalle_data)
            
        compra.actualizar_total()
        return compra

    @transaction.atomic
    def update(self, instance, validated_data):
        detalles_data = validated_data.pop('detalles', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if detalles_data is not None:
            # Eliminar detalles actuales y recrearlos (simplificado)
            instance.detalles.all().delete()
            for detalle_data in detalles_data:
                DetalleCompra.objects.create(compra=instance, **detalle_data)
            
            instance.actualizar_total()

        return instance


class DetalleNotaCreditoProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleNotaCreditoProveedor
        fields = '__all__'
        read_only_fields = ('id', 'nota_credito', 'subtotal')


class NotaCreditoProveedorSerializer(serializers.ModelSerializer):
    compra_numero = serializers.CharField(
        source='compra_original.id', read_only=True
    )
    detalles = DetalleNotaCreditoProveedorSerializer(many=True, required=False)

    class Meta:
        model  = NotaCreditoProveedor
        fields = '__all__'
        read_only_fields = ('id', 'numero', 'creado_en', 'total')

    @transaction.atomic
    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles', [])
        nota_credito = NotaCreditoProveedor.objects.create(**validated_data)
        
        for detalle_data in detalles_data:
            DetalleNotaCreditoProveedor.objects.create(nota_credito=nota_credito, **detalle_data)
            
        nota_credito.recalcular_totales()
        return nota_credito
