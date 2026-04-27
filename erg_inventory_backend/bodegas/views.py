from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from core.permissions import IsAdminOrReadOnly
from .models import Bodega, StockBodega
from .serializers import BodegaSerializer, StockBodegaSerializer, TransferenciaSerializer


class BodegaListCreateView(generics.ListCreateAPIView):
    queryset           = Bodega.objects.all()
    serializer_class   = BodegaSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['nombre', 'codigo', 'ciudad']


class BodegaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Bodega.objects.all()
    serializer_class   = BodegaSerializer
    permission_classes = [IsAdminOrReadOnly]


class StockBodegaListView(generics.ListAPIView):
    serializer_class   = StockBodegaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = StockBodega.objects.select_related('bodega', 'producto').all()
        bodega_id  = self.request.query_params.get('bodega_id')
        producto_id = self.request.query_params.get('producto_id')
        if bodega_id:   qs = qs.filter(bodega_id=bodega_id)
        if producto_id: qs = qs.filter(producto_id=producto_id)
        return qs


class TransferirStockView(APIView):
    """POST /api/bodegas/transferir/ — mueve stock de una bodega a otra."""
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        s = TransferenciaSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data

        if d['bodega_origen'] == d['bodega_destino']:
            return Response({'error': 'Las bodegas deben ser diferentes'}, status=400)

        origen = StockBodega.objects.select_for_update().filter(
            bodega_id=d['bodega_origen'], producto_id=d['producto']
        ).first()

        if not origen or origen.cantidad < d['cantidad']:
            return Response({'error': 'Stock insuficiente en la bodega origen'}, status=400)

        origen.cantidad -= d['cantidad']
        origen.save()

        destino, _ = StockBodega.objects.get_or_create(
            bodega_id=d['bodega_destino'], producto_id=d['producto']
        )
        destino.cantidad += d['cantidad']
        destino.save()

        return Response({'message': f'Transferencia exitosa: {d["cantidad"]} unidades movidas'})
