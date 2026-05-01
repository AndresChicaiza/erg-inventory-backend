# ── configuracion/views.py ────────────────────────────────────────────────────
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from core.permissions import IsAdmin, IsAdminOrContador, CanEditConfiguracion
from .models import ConfiguracionEmpresa, TarifaReteICA, TarifaRetefuente
from .serializers import (
    ConfiguracionEmpresaSerializer,
    TarifaReteICASerializer,
    TarifaRetefuenteSerializer,
)


class ConfiguracionView(APIView):
    """
    GET  /api/configuracion/  → obtener config de la empresa
    PATCH /api/configuracion/ → actualizar (solo Admin)
    """
    permission_classes = [CanEditConfiguracion]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        config = ConfiguracionEmpresa.objects.first()
        if not config:
            return Response({'error': 'Configuración no encontrada'}, status=404)
        return Response(ConfiguracionEmpresaSerializer(config).data)

    def patch(self, request):
        config = ConfiguracionEmpresa.objects.first()
        if not config:
            config = ConfiguracionEmpresa()
        s = ConfiguracionEmpresaSerializer(config, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)


class TarifaRetefuenteListView(generics.ListAPIView):
    queryset           = TarifaRetefuente.objects.filter(activo=True)
    serializer_class   = TarifaRetefuenteSerializer
    permission_classes = [IsAuthenticated]


class TarifaReteICAListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class   = TarifaReteICASerializer

    def get_queryset(self):
        ciudad = self.request.query_params.get('ciudad', '')
        qs = TarifaReteICA.objects.filter(activo=True)
        if ciudad:
            qs = qs.filter(ciudad__iexact=ciudad)
        return qs