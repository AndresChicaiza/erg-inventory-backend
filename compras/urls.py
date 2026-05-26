from django.urls import path
from .views import CompraListCreateView, CompraDetailView, RecibirCompraView, CancelarCompraView

urlpatterns = [
    path('',                   CompraListCreateView.as_view(), name='compra-list'),
    path('<int:pk>/',          CompraDetailView.as_view(),     name='compra-detail'),
    path('<int:pk>/recibir/',  RecibirCompraView.as_view(),    name='compra-recibir'),
    path('<int:pk>/cancelar/', CancelarCompraView.as_view(),   name='compra-cancelar'),
]
