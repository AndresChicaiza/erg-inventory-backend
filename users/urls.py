from django.urls import path
from .views import UsuarioListCreateView, UsuarioDetailView

urlpatterns = [
    path('',        UsuarioListCreateView.as_view(), name='usuario-list'),
    path('<int:pk>/', UsuarioDetailView.as_view(),   name='usuario-detail'),
]
