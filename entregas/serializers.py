from rest_framework import serializers
from .models import Entrega, DetalleEntrega


class DetalleEntregaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)

    class Meta:
        model  = DetalleEntrega
        fields = '__all__'
        read_only_fields = ('id',)


class EntregaSerializer(serializers.ModelSerializer):
    cliente_nombre    = serializers.CharField(source='cliente.nombre',    read_only=True)
    creado_por_nombre = serializers.CharField(source='creado_por.nombre', read_only=True)
    bodega_origen_nombre = serializers.CharField(source='bodega_origen.nombre', read_only=True)
    bodega_destino_nombre = serializers.CharField(source='bodega_destino.nombre', read_only=True)
    detalles          = DetalleEntregaSerializer(many=True)

    class Meta:
        model  = Entrega
        fields = '__all__'
        read_only_fields = ('id', 'creado_en', 'actualizado_en')

    def create(self, validated_data):
        detalles_data = validated_data.pop('detalles', [])
        entrega = Entrega.objects.create(**validated_data)
        
        for det_data in detalles_data:
            DetalleEntrega.objects.create(entrega=entrega, **det_data)
            
            # Si es un Traslado, descontar de bodega_origen inmediatamente
            if entrega.tipo_entrega == 'Traslado' and entrega.bodega_origen:
                from bodegas.models import StockBodega
                from movimientos.models import Movimiento
                
                prod = det_data['producto']
                cant = det_data['cantidad']
                
                sb = StockBodega.objects.filter(bodega=entrega.bodega_origen, producto=prod).first()
                if sb:
                    sb.cantidad = max(0, sb.cantidad - cant)
                    sb.save()
                    
                    # Registrar movimiento de salida
                    Movimiento.objects.create(
                        producto=prod,
                        bodega=entrega.bodega_origen,
                        tipo='Salida',
                        cantidad=cant,
                        referencia=f'Traslado Saliente ENT-{entrega.id:04d}',
                        observacion=f'Salida por traslado hacia {entrega.bodega_destino.nombre if entrega.bodega_destino else "Desconocida"}',
                        creado_por=entrega.creado_por
                    )
                    
                # También descontar del stock global del producto
                prod.stock = max(0, prod.stock - cant)
                prod.save()

        return entrega
