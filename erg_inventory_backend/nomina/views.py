from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from core.mixins import CreatedByMixin
from core.permissions import IsAdmin
from .models import PeriodoNomina, LineaNomina, ConceptoNomina
from .serializers import PeriodoNominaSerializer, LineaNominaSerializer, ConceptoNominaSerializer


class PeriodoNominaListCreateView(CreatedByMixin, generics.ListCreateAPIView):
    queryset           = PeriodoNomina.objects.prefetch_related('lineas__empleado').all()
    serializer_class   = PeriodoNominaSerializer
    permission_classes = [IsAdmin]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['nombre', 'estado']


class PeriodoNominaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = PeriodoNomina.objects.all()
    serializer_class   = PeriodoNominaSerializer
    permission_classes = [IsAdmin]


class LineaNominaListCreateView(generics.ListCreateAPIView):
    queryset           = LineaNomina.objects.select_related('empleado', 'periodo').all()
    serializer_class   = LineaNominaSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        qs = super().get_queryset()
        periodo_id = self.request.query_params.get('periodo_id')
        if periodo_id:
            qs = qs.filter(periodo_id=periodo_id)
        return qs


class LineaNominaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = LineaNomina.objects.all()
    serializer_class   = LineaNominaSerializer
    permission_classes = [IsAdmin]


class CerrarPeriodoView(APIView):
    """POST /api/nomina/periodos/<id>/cerrar/ — calcula totales y marca como Aprobada."""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            periodo = PeriodoNomina.objects.get(pk=pk)
        except PeriodoNomina.DoesNotExist:
            return Response({'error': 'Período no encontrado'}, status=404)

        agg = periodo.lineas.aggregate(
            dev=Sum('total_devengado'),
            ded=Sum('total_deducciones'),
            net=Sum('neto_pagar')
        )
        periodo.total_devengado   = agg['dev'] or 0
        periodo.total_deducciones = agg['ded'] or 0
        periodo.total_neto        = agg['net'] or 0
        periodo.estado = 'Aprobada'
        periodo.save()
        return Response(PeriodoNominaSerializer(periodo).data)


class ConceptoNominaListView(generics.ListCreateAPIView):
    queryset           = ConceptoNomina.objects.filter(activo=True)
    serializer_class   = ConceptoNominaSerializer
    permission_classes = [IsAdmin]
