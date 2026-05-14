from rest_framework import serializers
from django.utils import timezone
from .models import Producto, Lote


def _actualizar_estado_lote(lote):
    """Actualiza el campo estado del lote según su fecha de vencimiento y stock."""
    if not lote.fecha_vencimiento:
        return
    hoy = timezone.now().date()
    delta = (lote.fecha_vencimiento - hoy).days
    if lote.stock_disponible <= 0:
        nuevo = 'Agotado'
    elif delta < 0:
        nuevo = 'Vencido'
    elif delta <= 30:
        nuevo = 'Por Vencer'
    else:
        nuevo = 'Vigente'
    if lote.estado != nuevo:
        lote.estado = nuevo
        lote.save(update_fields=['estado'])


class LoteSerializer(serializers.ModelSerializer):
    dias_para_vencer = serializers.SerializerMethodField()

    class Meta:
        model  = Lote
        fields = '__all__'

    def get_dias_para_vencer(self, obj):
        return (obj.fecha_vencimiento - timezone.now().date()).days

    def to_representation(self, instance):
        # Auto-actualizar estado al leer el lote
        _actualizar_estado_lote(instance)
        return super().to_representation(instance)


class ProductoSerializer(serializers.ModelSerializer):
    estado_stock       = serializers.ReadOnlyField()
    precio_sin_iva     = serializers.ReadOnlyField()
    valor_iva_unitario = serializers.ReadOnlyField()
    lotes              = LoteSerializer(many=True, read_only=True)

    class Meta:
        model  = Producto
        fields = '__all__'
        read_only_fields = ('id', 'creado_en', 'actualizado_en')


class ProductoMiniSerializer(serializers.ModelSerializer):
    """Serializer liviano para selectores en factura."""
    precio_sin_iva     = serializers.ReadOnlyField()
    valor_iva_unitario = serializers.ReadOnlyField()

    class Meta:
        model  = Producto
        fields = (
            'id', 'codigo', 'codigo_barras', 'nombre', 'categoria',
            'precio_venta', 'precio_sin_iva', 'valor_iva_unitario',
            'iva_tipo', 'iva_incluido', 'unidad_medida',
            'stock', 'estado', 'controla_vencimiento',
        )