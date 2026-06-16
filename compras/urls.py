from django.urls import path
from .views import (
    CompraListCreateView, CompraDetailView, RecibirCompraView, CancelarCompraView,
    NotaCreditoProveedorListCreateView, NotaCreditoProveedorDetailView
)

urlpatterns = [
    path('',                   CompraListCreateView.as_view(), name='compra-list'),
    path('<int:pk>/',          CompraDetailView.as_view(),     name='compra-detail'),
    path('<int:pk>/recibir/',  RecibirCompraView.as_view(),    name='compra-recibir'),
    path('<int:pk>/cancelar/', CancelarCompraView.as_view(),   name='compra-cancelar'),
    path('notas-credito/',     NotaCreditoProveedorListCreateView.as_view(), name='compra-nc-list'),
    path('notas-credito/<int:pk>/', NotaCreditoProveedorDetailView.as_view(), name='compra-nc-detail'),
]
