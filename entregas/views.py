from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from core.mixins import CreatedByMixin
from .models import Entrega
from .serializers import EntregaSerializer


class EntregaListCreateView(CreatedByMixin, generics.ListCreateAPIView):
    serializer_class   = EntregaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['cliente__nombre', 'estado', 'transportista', 'numero_guia']
    ordering_fields    = ['creado_en', 'estado', 'fecha_estimada']

    def get_queryset(self):
        qs = Entrega.objects.select_related(
            'cliente', 'creado_por', 'bodega_origen', 'bodega_destino'
        ).prefetch_related('detalles').all()

        tipo = self.request.query_params.get('tipo_entrega')
        if tipo:
            qs = qs.filter(tipo_entrega=tipo)

        return qs

    def get_permissions(self):
        from core.permissions import CanEditEnvio
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [CanEditEnvio()]


class EntregaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Entrega.objects.select_related(
        'cliente', 'bodega_origen', 'bodega_destino'
    ).prefetch_related('detalles').all()
    serializer_class   = EntregaSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        from core.permissions import CanEditEnvio
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [CanEditEnvio()]


class RecibirTrasladoView(APIView):
    """POST /api/entregas/<id>/recibir/"""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        try:
            entrega = Entrega.objects.get(pk=pk, tipo_entrega='Traslado')
        except Entrega.DoesNotExist:
            return Response({'error': 'Traslado no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if entrega.estado == 'Entregada':
            return Response({'error': 'El traslado ya fue recibido'}, status=status.HTTP_400_BAD_REQUEST)

        # Sumar stock a bodega destino
        from bodegas.models import StockBodega
        from movimientos.models import Movimiento

        if not entrega.bodega_destino:
            return Response({'error': 'La entrega no tiene bodega de destino'}, status=status.HTTP_400_BAD_REQUEST)

        for detalle in entrega.detalles.all():
            sb, created = StockBodega.objects.get_or_create(
                bodega=entrega.bodega_destino,
                producto=detalle.producto,
                defaults={'cantidad': 0}
            )
            sb.cantidad += detalle.cantidad
            sb.save()

            # Movimiento de entrada
            Movimiento.objects.create(
                producto=detalle.producto,
                bodega=entrega.bodega_destino,
                tipo='Entrada',
                cantidad=detalle.cantidad,
                referencia=f'Traslado Entrante ENT-{entrega.id:04d}',
                observacion=f'Ingreso por traslado desde {entrega.bodega_origen.nombre if entrega.bodega_origen else "Desconocida"}',
                creado_por=request.user
            )

            # Sumar al stock global
            detalle.producto.stock += detalle.cantidad
            detalle.producto.save()

        entrega.estado = 'Entregada'
        from django.utils import timezone
        entrega.fecha_entregada = timezone.now().date()
        entrega.save(update_fields=['estado', 'fecha_entregada'])

        return Response({'mensaje': 'Traslado recibido correctamente'})
