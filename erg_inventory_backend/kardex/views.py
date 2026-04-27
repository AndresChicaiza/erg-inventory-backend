from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from movimientos.models import Movimiento
from productos.models import Producto


class KardexListView(APIView):
    """
    Devuelve el kardex completo o filtrado por producto.
    GET /api/kardex/?producto_id=3
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        producto_id = request.query_params.get('producto_id')

        movs = (
            Movimiento.objects
            .select_related('producto', 'creado_por')
            .order_by('producto_id', 'id')
        )
        if producto_id:
            movs = movs.filter(producto_id=producto_id)

        saldos = {}
        resultado = []

        for mov in movs:
            pid = mov.producto_id
            saldos.setdefault(pid, 0)

            entrada = salida = None
            if mov.tipo == 'Entrada':
                saldos[pid] += mov.cantidad
                entrada = mov.cantidad
            elif mov.tipo == 'Salida':
                saldos[pid] -= mov.cantidad
                salida = mov.cantidad
            else:  # Ajuste
                saldos[pid] = mov.cantidad

            resultado.append({
                'id':              mov.id,
                'fecha':           mov.fecha,
                'producto_id':     pid,
                'producto':        mov.producto.nombre,
                'producto_codigo': mov.producto.codigo,
                'tipo':            mov.tipo,
                'entrada':         entrada,
                'salida':          salida,
                'saldo':           saldos[pid],
                'referencia':      mov.referencia,
                'observacion':     mov.observacion,
                'creado_por':      mov.creado_por.nombre if mov.creado_por else None,
            })

        return Response(resultado)


class KardexProductosView(APIView):
    """Lista de productos que tienen al menos un movimiento."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ids = Movimiento.objects.values_list('producto_id', flat=True).distinct()
        productos = Producto.objects.filter(id__in=ids).values('id', 'codigo', 'nombre')
        return Response(list(productos))
