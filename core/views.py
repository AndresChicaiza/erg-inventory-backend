from rest_framework import viewsets, permissions, views
from rest_framework.response import Response
from django.db.models import Q
from .models import AuditLog
from .serializers import AuditLogSerializer

from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
import datetime
from django.utils import timezone

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Solo lectura para administradores."""
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = AuditLog.objects.select_related('usuario').all()
        
        # Filtros
        accion = self.request.query_params.get('accion')
        if accion:
            qs = qs.filter(accion=accion)
            
        modulo = self.request.query_params.get('modulo')
        if modulo:
            qs = qs.filter(modulo=modulo)
            
        usuario = self.request.query_params.get('usuario')
        if usuario:
            qs = qs.filter(usuario_id=usuario)
            
        ip = self.request.query_params.get('ip')
        if ip:
            qs = qs.filter(ip_address__icontains=ip)

        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            qs = qs.filter(fecha__date__gte=fecha_desde)
            
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_hasta:
            qs = qs.filter(fecha__date__lte=fecha_hasta)
            
        hora_desde = self.request.query_params.get('hora_desde')
        if hora_desde:
            qs = qs.filter(fecha__time__gte=hora_desde)
            
        hora_hasta = self.request.query_params.get('hora_hasta')
        if hora_hasta:
            qs = qs.filter(fecha__time__lte=hora_hasta)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(descripcion__icontains=search) |
                Q(usuario__nombre__icontains=search) |
                Q(modelo__icontains=search) |
                Q(modulo__icontains=search)
            )

        return qs

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        from django.db.models import Count
        
        hoy = timezone.now().date()
        logs_hoy = AuditLog.objects.filter(fecha__date=hoy)
        
        total_hoy = logs_hoy.count()
        usuarios_activos_hoy = logs_hoy.values('usuario').distinct().count()
        
        acciones = AuditLog.objects.values('accion').annotate(count=Count('id')).order_by('-count')
        modulos = AuditLog.objects.values('modulo').annotate(count=Count('id')).order_by('-count')
        
        return Response({
            'total_hoy': total_hoy,
            'usuarios_activos_hoy': usuarios_activos_hoy,
            'acciones': list(acciones),
            'modulos': list(modulos),
        })


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


from .ia_chatbot import responder_consulta_ia
from .ia_prediccion import calcular_predicciones_demanda

class IAChatView(views.APIView):
    """POST /api/core/ia/chat/"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        query_text = request.data.get('query', '')
        if not query_text:
            return Response({'error': 'La consulta no puede estar vacía.'}, status=400)
        
        response_data = responder_consulta_ia(query_text)
        return Response(response_data)


class IAPrediccionesView(views.APIView):
    """GET /api/core/ia/predicciones/"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = calcular_predicciones_demanda()
        return Response(data)
