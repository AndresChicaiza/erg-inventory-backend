from django.urls import path
from .views import (
    MeView,
    SedeListCreateView, SedeDetailView,
    UsuarioListCreateView, UsuarioDetailView,
)

urlpatterns = [
    # Auth
    path('auth/me/', MeView.as_view(), name='auth-me'),

    # Sedes
    path('sedes/',       SedeListCreateView.as_view(), name='sede-list'),
    path('sedes/<int:pk>/', SedeDetailView.as_view(),  name='sede-detail'),

    # Usuarios
    path('usuarios/',          UsuarioListCreateView.as_view(), name='usuario-list'),
    path('usuarios/<int:pk>/', UsuarioDetailView.as_view(),     name='usuario-detail'),
]