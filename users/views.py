from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from core.permissions import IsAdmin
from .models import Usuario
from .serializers import UsuarioSerializer, UsuarioCreateSerializer, UsuarioUpdateSerializer


# ── Auth ─────────────────────────────────────────────────────────────

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email    = request.data.get('email', '').strip()
        password = request.data.get('password', '')

        if not email or not password:
            return Response({'error': 'Email y contraseña requeridos'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({'error': 'Credenciales inválidas'},
                            status=status.HTTP_401_UNAUTHORIZED)
        if user.estado == 'Inactivo':
            return Response({'error': 'Usuario inactivo. Contacta al administrador.'},
                            status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user':    UsuarioSerializer(user).data,
        })


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


# ── CRUD Usuarios ────────────────────────────────────────────────────

class UsuarioListCreateView(generics.ListCreateAPIView):
    queryset = Usuario.objects.all().order_by('nombre')

    def get_permissions(self):
        return [IsAdmin()] if self.request.method == 'POST' else [IsAuthenticated()]

    def get_serializer_class(self):
        return UsuarioCreateSerializer if self.request.method == 'POST' else UsuarioSerializer


class UsuarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Usuario.objects.all()
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        return UsuarioUpdateSerializer if self.request.method in ('PUT', 'PATCH') else UsuarioSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if user == request.user:
            return Response({'error': 'No puedes eliminarte a ti mismo'},
                            status=status.HTTP_400_BAD_REQUEST)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
