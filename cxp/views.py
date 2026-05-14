from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Count, Q
from core.mixins import CreatedByMixin, AuditMixin
from .models import CuentaPorPagar, PagoCXP
from .serializers import CXPSerializer, PagoCXPSerializer


class CXPListCreateView(AuditMixin, CreatedByMixin, generics.ListCreateAPIView):
    serializer_class   = CXPSerializer
    permission_classes = [IsAuthenticated]
    audit_modulo       = 'Finanzas'
    audit_modelo       = 'CXP'
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    # ✅ Fix: busca por razon_social en lugar de empresa
    search_fields      = ['proveedor__razon_social', 'proveedor__numero_documento', 'concepto', 'estado']
    ordering_fields    = ['fecha_emision', 'fecha_vencimiento', 'monto_total', 'saldo']

    def get_queryset(self):
        qs = CuentaPorPagar.objects.select_related(
            'proveedor', 'creado_por'
        ).prefetch_related('pagos').all()

        # Marcar automáticamente como Vencidas
        hoy = timezone.now().date()
        qs.filter(
            estado__in=['Pendiente', 'Parcial'],
            fecha_vencimiento__lt=hoy
        ).update(estado='Vencida')

        # Filtros opcionales
        estado = self.request.query_params.get('estado')
        if estado:
            qs = qs.filter(estado=estado)

        proveedor = self.request.query_params.get('proveedor')
        if proveedor:
            qs = qs.filter(proveedor_id=proveedor)

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


class CXPDetailView(AuditMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset           = CuentaPorPagar.objects.select_related('proveedor').prefetch_related('pagos').all()
    serializer_class   = CXPSerializer
    permission_classes = [IsAuthenticated]
    audit_modulo       = 'Finanzas'
    audit_modelo       = 'CXP'


class PagoCXPCreateView(AuditMixin, CreatedByMixin, generics.CreateAPIView):
    queryset           = PagoCXP.objects.all()
    serializer_class   = PagoCXPSerializer
    permission_classes = [IsAuthenticated]
    audit_modulo       = 'Finanzas'
    audit_modelo       = 'Pago CXP'

    def create(self, request, *args, **kwargs):
        cxp_id = request.data.get('cxp')
        monto  = float(request.data.get('monto', 0))
        try:
            cxp = CuentaPorPagar.objects.get(id=cxp_id)
            if monto > float(cxp.saldo):
                return Response(
                    {'error': f'El monto supera el saldo pendiente (${cxp.saldo})'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except CuentaPorPagar.DoesNotExist:
            return Response({'error': 'CXP no encontrada'}, status=404)
        return super().create(request, *args, **kwargs)


class CXPResumenView(APIView):
    """
    GET /api/cxp/resumen/
    Totales para el encabezado del módulo.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hoy  = timezone.now().date()
        qs   = CuentaPorPagar.objects.all()
        prox = hoy + timezone.timedelta(days=7)

        data = {
            'total_por_pagar': qs.filter(
                estado__in=['Pendiente', 'Parcial']
            ).aggregate(t=Sum('saldo'))['t'] or 0,

            'total_vencido': qs.filter(
                estado='Vencida'
            ).aggregate(t=Sum('saldo'))['t'] or 0,

            'total_pagado_mes': PagoCXP.objects.filter(
                fecha__year=hoy.year, fecha__month=hoy.month
            ).aggregate(t=Sum('monto'))['t'] or 0,

            'proximas_vencer': qs.filter(
                estado__in=['Pendiente', 'Parcial'],
                fecha_vencimiento__gte=hoy,
                fecha_vencimiento__lte=prox,
            ).count(),

            'por_estado': {
                e: qs.filter(estado=e).count()
                for e, _ in CuentaPorPagar.ESTADO_CHOICES
            },
        }
        return Response(data)


class CXPPorProveedorView(APIView):
    """
    GET /api/cxp/por-proveedor/
    Resumen de obligaciones agrupadas por proveedor.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.db.models import F
        resultado = (
            CuentaPorPagar.objects
            .filter(estado__in=['Pendiente', 'Parcial', 'Vencida'])
            .values(
                'proveedor__id',
                'proveedor__razon_social',
                'proveedor__numero_documento',
            )
            .annotate(
                total_saldo=Sum('saldo'),
                num_facturas=Count('id'),
            )
            .order_by('-total_saldo')
        )
        return Response(list(resultado))