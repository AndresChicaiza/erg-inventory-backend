from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from core.permissions import CanMovimientoInventario
from .models import Movimiento
from .serializers import MovimientoSerializer


class MovimientoListCreateView(generics.ListCreateAPIView):
    queryset           = Movimiento.objects.select_related('producto', 'creado_por').all()
    serializer_class   = MovimientoSerializer
    permission_classes = [CanMovimientoInventario]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['producto__nombre', 'tipo', 'referencia']
    ordering_fields    = ['fecha', 'tipo']

    @transaction.atomic
    def perform_create(self, serializer):
        numero_lote = serializer.validated_data.pop('numero_lote', None)
        fecha_vencimiento = serializer.validated_data.pop('fecha_vencimiento', None)

        mov = serializer.save(creado_por=self.request.user)
        producto = mov.producto

        from rest_framework.exceptions import ValidationError

        if producto.controla_vencimiento and mov.tipo in ['Entrada', 'Salida']:
            if not numero_lote:
                raise ValidationError({"numero_lote": "Este producto requiere especificar un número de lote."})
            
            from productos.models import Lote
            
            if mov.tipo == 'Entrada':
                if not fecha_vencimiento:
                    # Intenta buscar el lote existente para no pedir fecha, o exige la fecha si es nuevo
                    lote_existente = Lote.objects.filter(producto=producto, numero_lote=numero_lote).first()
                    if not lote_existente:
                        raise ValidationError({"fecha_vencimiento": "Para ingresar un nuevo lote se requiere la fecha de vencimiento."})
                    fecha_vencimiento = lote_existente.fecha_vencimiento

                lote_obj, created = Lote.objects.get_or_create(
                    producto=producto, numero_lote=numero_lote,
                    defaults={'fecha_vencimiento': fecha_vencimiento}
                )
                lote_obj.stock_disponible += mov.cantidad
                lote_obj.save()
                mov.lote = lote_obj
                mov.save(update_fields=['lote'])

            elif mov.tipo == 'Salida':
                lote_obj = Lote.objects.filter(producto=producto, numero_lote=numero_lote).first()
                if not lote_obj:
                    raise ValidationError({"numero_lote": "Lote no encontrado para este producto."})
                if lote_obj.stock_disponible < mov.cantidad:
                    raise ValidationError({"cantidad": f"Stock insuficiente en el lote {numero_lote}. Disponible: {lote_obj.stock_disponible}"})
                
                lote_obj.stock_disponible -= mov.cantidad
                lote_obj.save()
                mov.lote = lote_obj
                mov.save(update_fields=['lote'])

        if mov.tipo == 'Entrada':
            producto.stock += mov.cantidad
        elif mov.tipo == 'Salida':
            producto.stock = max(0, producto.stock - mov.cantidad)
        elif mov.tipo == 'Ajuste':
            producto.stock = mov.cantidad

        producto.save(update_fields=['stock'])


class MovimientoDetailView(generics.RetrieveAPIView):
    queryset           = Movimiento.objects.select_related('producto').all()
    serializer_class   = MovimientoSerializer
    permission_classes = [IsAuthenticated]