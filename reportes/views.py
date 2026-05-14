from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, F, Q


class ResumenView(APIView):
    """Dashboard general — GET /api/reportes/resumen/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from ventas.models import Venta
        from compras.models import Compra
        from productos.models import Producto
        from clientes.models import Cliente
        from proveedores.models import Proveedor
        from movimientos.models import Movimiento
        from entregas.models import Entrega

        # Totales monetarios
        total_ventas  = Venta.objects.aggregate(t=Sum('total'))['t']  or 0
        total_compras = Compra.objects.aggregate(t=Sum('total'))['t'] or 0

        # Ventas por estado
        ventas_estado = (
            Venta.objects.values('estado')
            .annotate(cantidad=Count('id'), monto=Sum('total'))
        )

        # Compras por estado
        compras_estado = (
            Compra.objects.values('estado')
            .annotate(cantidad=Count('id'), monto=Sum('total'))
        )

        # Stock
        stock_bajo   = Producto.objects.filter(stock__gt=0, stock__lte=F('stock_minimo'))
        sin_stock    = Producto.objects.filter(stock=0)
        top_stock    = (
            Producto.objects
            .filter(estado='Activo')
            .order_by('-stock')[:5]
            .values('nombre', 'stock', 'categoria')
        )

        # Movimientos por tipo
        movs_tipo = (
            Movimiento.objects.values('tipo')
            .annotate(cantidad=Count('id'))
        )

        # Entregas por estado
        entregas_estado = (
            Entrega.objects.values('estado')
            .annotate(cantidad=Count('id'))
        )

        return Response({
            # Monetarios
            'total_ventas':  float(total_ventas),
            'total_compras': float(total_compras),
            'utilidad_bruta': float(total_ventas - total_compras),

            # Conteos generales
            'num_ventas':      Venta.objects.count(),
            'num_compras':     Compra.objects.count(),
            'num_productos':   Producto.objects.count(),
            'num_clientes':    Cliente.objects.count(),
            'num_proveedores': Proveedor.objects.count(),
            'num_movimientos': Movimiento.objects.count(),

            # Stock
            'productos_stock_bajo': stock_bajo.count(),
            'productos_sin_stock':  sin_stock.count(),
            'top_stock': list(top_stock),

            # Detalles por estado
            'ventas_por_estado':    list(ventas_estado),
            'compras_por_estado':   list(compras_estado),
            'entregas_por_estado':  list(entregas_estado),
            'movimientos_por_tipo': list(movs_tipo),
        })


class FlujoCajaView(APIView):
    """GET /api/reportes/flujo-caja/ — resumen financiero cruzado de CXC y CXP"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.utils import timezone
        import datetime
        from cxc.models import CuentaPorCobrar
        from cxp.models import CuentaPorPagar

        hoy  = timezone.now().date()
        d7   = hoy + datetime.timedelta(days=7)
        d30  = hoy + datetime.timedelta(days=30)

        # ── CXC (por cobrar) ──
        cxc_qs = CuentaPorCobrar.objects.exclude(estado__in=['Pagada', 'Anulada'])
        cxc_total   = cxc_qs.aggregate(t=Sum('saldo'))['t'] or 0
        cxc_vencida = cxc_qs.filter(fecha_vencimiento__lt=hoy).aggregate(t=Sum('saldo'))['t'] or 0
        cxc_semana  = cxc_qs.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=d7).aggregate(t=Sum('saldo'))['t'] or 0
        cxc_mes     = cxc_qs.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=d30).aggregate(t=Sum('saldo'))['t'] or 0

        # ── CXP (por pagar) ──
        cxp_qs = CuentaPorPagar.objects.exclude(estado__in=['Pagada', 'Anulada'])
        cxp_total   = cxp_qs.aggregate(t=Sum('saldo'))['t'] or 0
        cxp_vencida = cxp_qs.filter(fecha_vencimiento__lt=hoy).aggregate(t=Sum('saldo'))['t'] or 0
        cxp_semana  = cxp_qs.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=d7).aggregate(t=Sum('saldo'))['t'] or 0
        cxp_mes     = cxp_qs.filter(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=d30).aggregate(t=Sum('saldo'))['t'] or 0

        # ── Top 5 clientes con mayor cartera ──
        top_clientes = list(
            cxc_qs.values('cliente__razon_social')
            .annotate(saldo_total=Sum('saldo'))
            .order_by('-saldo_total')[:5]
        )

        # ── Top 5 proveedores con mayor deuda ──
        top_proveedores = list(
            cxp_qs.values('proveedor__razon_social')
            .annotate(saldo_total=Sum('saldo'))
            .order_by('-saldo_total')[:5]
        )

        return Response({
            'cxc': {
                'total_pendiente': float(cxc_total),
                'vencida':         float(cxc_vencida),
                'proxima_semana':  float(cxc_semana),
                'proximo_mes':     float(cxc_mes),
                'num_cuentas':     cxc_qs.count(),
            },
            'cxp': {
                'total_pendiente': float(cxp_total),
                'vencida':         float(cxp_vencida),
                'proxima_semana':  float(cxp_semana),
                'proximo_mes':     float(cxp_mes),
                'num_cuentas':     cxp_qs.count(),
            },
            'posicion_neta':   float(cxc_total) - float(cxp_total),
            'top_clientes':    top_clientes,
            'top_proveedores': top_proveedores,
        })
