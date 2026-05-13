from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from .models import Receta, IngredienteReceta, OrdenProduccion, ConsumoProduccion
from .serializers import (
    RecetaSerializer, IngredienteRecetaSerializer,
    OrdenProduccionSerializer, ConsumoProduccionSerializer
)

class RecetaListCreateView(generics.ListCreateAPIView):
    queryset = Receta.objects.all()
    serializer_class = RecetaSerializer
    permission_classes = [IsAuthenticated]

class RecetaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Receta.objects.all()
    serializer_class = RecetaSerializer
    permission_classes = [IsAuthenticated]

class IngredienteRecetaListCreateView(generics.ListCreateAPIView):
    serializer_class = IngredienteRecetaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return IngredienteReceta.objects.filter(receta_id=self.kwargs['receta_id'])

    def perform_create(self, serializer):
        receta = Receta.objects.get(pk=self.kwargs['receta_id'])
        serializer.save(receta=receta)

class IngredienteRecetaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = IngredienteReceta.objects.all()
    serializer_class = IngredienteRecetaSerializer
    permission_classes = [IsAuthenticated]

class OrdenProduccionListCreateView(generics.ListCreateAPIView):
    queryset = OrdenProduccion.objects.select_related('receta__producto_terminado', 'creado_por').prefetch_related('consumos').all()
    serializer_class = OrdenProduccionSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def perform_create(self, serializer):
        orden = serializer.save(creado_por=self.request.user)
        # Generar consumos esperados automáticamente
        for ingrediente in orden.receta.ingredientes.all():
            cantidad_esperada = ingrediente.cantidad_esperada * orden.cantidad_a_fabricar
            ConsumoProduccion.objects.create(
                orden=orden,
                producto_materia=ingrediente.producto_materia,
                cantidad_esperada=cantidad_esperada,
                cantidad_real=cantidad_esperada  # Por defecto el operario usará lo esperado
            )

class OrdenProduccionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = OrdenProduccion.objects.all()
    serializer_class = OrdenProduccionSerializer
    permission_classes = [IsAuthenticated]

class CompletarOrdenProduccionView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        try:
            orden = OrdenProduccion.objects.get(pk=pk)
        except OrdenProduccion.DoesNotExist:
            return Response({'error': 'Orden no encontrada'}, status=404)

        if orden.estado == 'Completada':
            return Response({'error': 'La orden ya está completada'}, status=400)

        # 1. Actualizar consumos reales si se enviaron en el request
        # Formato esperado: {'consumos': [{'id': 1, 'cantidad_real': 2.5}, ...]}
        consumos_data = request.data.get('consumos', [])
        for c_data in consumos_data:
            consumo = ConsumoProduccion.objects.get(pk=c_data['id'], orden=orden)
            consumo.cantidad_real = c_data['cantidad_real']
            consumo.save(update_fields=['cantidad_real'])

        # 2. Descontar materia prima del inventario
        from bodegas.models import StockBodega
        from movimientos.models import Movimiento

        for consumo in orden.consumos.all():
            producto = consumo.producto_materia
            cantidad = consumo.cantidad_real
            
            producto.stock -= cantidad
            producto.save(update_fields=['stock'])

            if orden.bodega:
                sb, created = StockBodega.objects.get_or_create(bodega=orden.bodega, producto=producto)
                sb.cantidad -= cantidad
                sb.save()

            Movimiento.objects.create(
                producto=producto, tipo='Salida', cantidad=cantidad,
                referencia=orden.numero,
                observacion=f'Consumo para OP {orden.numero}',
                creado_por=request.user
            )

        # 3. Sumar producto terminado al inventario
        producto_terminado = orden.receta.producto_terminado
        cantidad_fabricada = orden.cantidad_a_fabricar
        
        producto_terminado.stock += cantidad_fabricada
        producto_terminado.save(update_fields=['stock'])
        
        if orden.bodega:
            sb, created = StockBodega.objects.get_or_create(bodega=orden.bodega, producto=producto_terminado)
            sb.cantidad += cantidad_fabricada
            sb.save()

        Movimiento.objects.create(
            producto=producto_terminado, tipo='Entrada', cantidad=cantidad_fabricada,
            referencia=orden.numero,
            observacion=f'Producción completada OP {orden.numero}',
            creado_por=request.user
        )

        # 4. Actualizar estado
        orden.estado = 'Completada'
        orden.save(update_fields=['estado', 'fecha_fin'])

        # Si viene de una factura pendiente, podríamos intentar ver si ya se puede entregar, 
        # pero eso ya es logística.
        return Response({'mensaje': 'Orden completada y stock actualizado'})
