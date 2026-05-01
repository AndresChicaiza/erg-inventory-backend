from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdmin, IsAdminOrContador
from .models import Usuario, Sede
from .serializers import (
    SedeSerializer, UsuarioSerializer,
    UsuarioCreateSerializer, UsuarioMeSerializer
)


# ── Auth: quién soy ───────────────────────────────────────────────────────────

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UsuarioMeSerializer(request.user).data)


# ── Sedes ─────────────────────────────────────────────────────────────────────

class SedeListCreateView(generics.ListCreateAPIView):
    queryset           = Sede.objects.all()
    serializer_class   = SedeSerializer
    permission_classes = [IsAdminOrContador]
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['nombre', 'tipo', 'ciudad']


class SedeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Sede.objects.all()
    serializer_class   = SedeSerializer
    permission_classes = [IsAdmin]


# ── Usuarios ──────────────────────────────────────────────────────────────────

class UsuarioListCreateView(generics.ListCreateAPIView):
    queryset           = Usuario.objects.select_related('sede').all()
    permission_classes = [IsAdmin]
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['nombre', 'email', 'rol']
    ordering_fields    = ['nombre', 'rol', 'creado_en']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UsuarioCreateSerializer
        return UsuarioSerializer


class UsuarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Usuario.objects.select_related('sede').all()
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UsuarioCreateSerializer
        return UsuarioSerializer

    def destroy(self, request, *args, **kwargs):
        """No eliminar — solo desactivar."""
        user = self.get_object()
        if user == request.user:
            return Response(
                {'error': 'No puedes desactivarte a ti mismo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.estado   = 'Inactivo'
        user.is_active = False
        user.save()
        return Response({'mensaje': 'Usuario desactivado'}, status=status.HTTP_200_OK)