from django.urls import path
from .views import VentaListCreateView, VentaDetailView

urlpatterns = [
    path('',          VentaListCreateView.as_view(), name='venta-list'),
    path('<int:pk>/', VentaDetailView.as_view(),     name='venta-detail'),
]
