from rest_framework import viewsets, permissions, views
from rest_framework.response import Response
from django.db.models import Q
from .models import AuditLog
from .serializers import AuditLogSerializer

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Solo lectura para administradores."""
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['accion', 'modulo', 'usuario']


class GlobalSearchView(views.APIView):
    """Búsqueda global en múltiples modelos."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return Response([])

        results = []

        # 1. Productos
        from productos.models import Producto
        prods = Producto.objects.filter(
            Q(nombre__icontains=query) | Q(codigo__icontains=query) | Q(codigo_barras__icontains=query)
        )[:5]
        for p in prods:
            results.append({
                'type': 'Producto',
                'id': p.id,
                'title': p.nombre,
                'subtitle': f"Código: {p.codigo} | Stock: {p.stock}",
                'link': f"/productos",
                'icon': '📦'
            })

        # 2. Clientes
        from clientes.models import Cliente
        clis = Cliente.objects.filter(
            Q(razon_social__icontains=query) | Q(nit_cedula__icontains=query)
        )[:5]
        for c in clis:
            results.append({
                'type': 'Cliente',
                'id': c.id,
                'title': c.razon_social,
                'subtitle': f"NIT/CC: {c.nit_cedula}",
                'link': f"/clientes",
                'icon': '👥'
            })

        # 3. Facturas
        from facturacion.models import Factura
        facts = Factura.objects.filter(
            Q(numero_factura__icontains=query) | Q(cliente__razon_social__icontains=query)
        )[:5]
        for f in facts:
            results.append({
                'type': 'Factura',
                'id': f.id,
                'title': f.numero_factura or f"Factura #{f.id}",
                'subtitle': f"Cliente: {f.cliente.razon_social} | Total: ${float(f.total):,.0f}",
                'link': f"/facturas",
                'icon': '🧾'
            })

        # 4. Empleados
        from nomina.models import Empleado
        emps = Empleado.objects.filter(
            Q(nombre__icontains=query) | Q(cedula__icontains=query)
        )[:5]
        for e in emps:
            results.append({
                'type': 'Empleado',
                'id': e.id,
                'title': e.nombre,
                'subtitle': f"Cargo: {e.cargo} | Cédula: {e.cedula}",
                'link': f"/empleados",
                'icon': '👨‍💼'
            })

        return Response(results)
