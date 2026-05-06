from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Count, Q
from core.mixins import CreatedByMixin
from .models import CuentaPorCobrar, PagoCXC
from .serializers import CXCSerializer, PagoCXCSerializer


class CXCListCreateView(CreatedByMixin, generics.ListCreateAPIView):
    serializer_class   = CXCSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    # ✅ Fix: busca por razon_social en lugar de nombre
    search_fields      = ['cliente__razon_social', 'cliente__numero_documento', 'concepto', 'estado']
    ordering_fields    = ['fecha_emision', 'fecha_vencimiento', 'monto_total', 'saldo']

    def get_queryset(self):
        qs = CuentaPorCobrar.objects.select_related(
            'cliente', 'creado_por'
        ).prefetch_related('pagos').all()

        # Marcar automáticamente como Vencidas las que pasaron su fecha
        hoy = timezone.now().date()
        qs.filter(
            estado__in=['Pendiente', 'Parcial'],
            fecha_vencimiento__lt=hoy
        ).update(estado='Vencida')

        # Filtros opcionales por query params
        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            qs = qs.filter(fecha_emision__gte=fecha_desde)

        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_hasta:
            qs = qs.filter(fecha_emision__lte=fecha_hasta)

        vence_desde = self.request.query_params.get('vence_desde')
        if vence_desde:
            qs = qs.filter(fecha_vencimiento__gte=vence_desde)

        vence_hasta = self.request.query_params.get('vence_hasta')
        if vence_hasta:
            qs = qs.filter(fecha_vencimiento__lte=vence_hasta)

        return qs


class CXCDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = CuentaPorCobrar.objects.select_related('cliente').prefetch_related('pagos').all()
    serializer_class   = CXCSerializer
    permission_classes = [IsAuthenticated]


class PagoCXCCreateView(CreatedByMixin, generics.CreateAPIView):
    queryset           = PagoCXC.objects.all()
    serializer_class   = PagoCXCSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        cxc_id = request.data.get('cxc')
        monto  = float(request.data.get('monto', 0))
        try:
            cxc = CuentaPorCobrar.objects.get(id=cxc_id)
            if monto > float(cxc.saldo):
                return Response(
                    {'error': f'El monto supera el saldo pendiente (${cxc.saldo})'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except CuentaPorCobrar.DoesNotExist:
            return Response({'error': 'CXC no encontrada'}, status=404)
        return super().create(request, *args, **kwargs)


class CXCResumenView(APIView):
    """
    GET /api/cxc/resumen/
    Devuelve totales para el encabezado del módulo.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hoy  = timezone.now().date()
        qs   = CuentaPorCobrar.objects.all()
        prox = hoy + timezone.timedelta(days=7)

        data = {
            'total_pendiente': qs.filter(
                estado__in=['Pendiente', 'Parcial']
            ).aggregate(t=Sum('saldo'))['t'] or 0,

            'total_vencido': qs.filter(
                estado='Vencida'
            ).aggregate(t=Sum('saldo'))['t'] or 0,

            'total_cobrado_mes': PagoCXC.objects.filter(
                fecha__year=hoy.year, fecha__month=hoy.month
            ).aggregate(t=Sum('monto'))['t'] or 0,

            'proximas_vencer': qs.filter(
                estado__in=['Pendiente', 'Parcial'],
                fecha_vencimiento__gte=hoy,
                fecha_vencimiento__lte=prox,
            ).count(),

            'por_estado': {
                e: qs.filter(estado=e).count()
                for e, _ in CuentaPorCobrar.ESTADO_CHOICES
            },
        }
        return Response(data)