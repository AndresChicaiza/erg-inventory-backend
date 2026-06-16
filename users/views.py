from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdmin, IsAdminOrContador
from core.mixins import AuditMixin
from .models import Usuario, Sede
from .serializers import (
    SedeSerializer, UsuarioSerializer,
    UsuarioCreateSerializer, UsuarioMeSerializer
)


from rest_framework_simplejwt.views import TokenObtainPairView
from core.utils import log_action

# ── Auth: quién soy ───────────────────────────────────────────────────────────

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UsuarioMeSerializer(request.user).data)


class LoggedTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            email = request.data.get('email')
            try:
                user = Usuario.objects.get(email=email)
                log_action(
                    user=user,
                    action='LOGIN',
                    modulo='Autenticación',
                    modelo='Usuario',
                    objeto_id=user.id,
                    descripcion=f"Inicio de sesión exitoso para {user.nombre}",
                    request=request
                )
            except Usuario.DoesNotExist:
                pass
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        log_action(
            user=request.user,
            action='LOGOUT',
            modulo='Autenticación',
            modelo='Usuario',
            objeto_id=request.user.id,
            descripcion=f"Cierre de sesión para {request.user.nombre}",
            request=request
        )
        return Response({'mensaje': 'Sesión cerrada correctamente'})


# ── Sedes ─────────────────────────────────────────────────────────────────────

class SedeListCreateView(generics.ListCreateAPIView):
    queryset           = Sede.objects.all()
    serializer_class   = SedeSerializer
    # permission_classes = [IsAdminOrContador] (se maneja en get_permissions)
    filter_backends    = [filters.SearchFilter]
    search_fields      = ['nombre', 'tipo', 'ciudad']

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdmin()]


class SedeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset           = Sede.objects.all()
    serializer_class   = SedeSerializer
    permission_classes = [IsAdmin]


# ── Usuarios ──────────────────────────────────────────────────────────────────

class UsuarioListCreateView(AuditMixin, generics.ListCreateAPIView):
    queryset           = Usuario.objects.select_related('sede').all()
    # permission_classes = [IsAdmin] (se maneja en get_permissions)
    filter_backends    = [filters.SearchFilter, filters.OrderingFilter]
    search_fields      = ['nombre', 'email', 'rol']
    ordering_fields    = ['nombre', 'rol', 'creado_en']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UsuarioCreateSerializer
        return UsuarioSerializer
        
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsAdmin()]


class UsuarioDetailView(AuditMixin, generics.RetrieveUpdateDestroyAPIView):
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