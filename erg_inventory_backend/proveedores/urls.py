from django.urls import path
from .views import ProveedorListCreateView, ProveedorDetailView

urlpatterns = [
    path('',          ProveedorListCreateView.as_view(), name='proveedor-list'),
    path('<int:pk>/', ProveedorDetailView.as_view(),     name='proveedor-detail'),
]
