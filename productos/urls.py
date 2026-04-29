from django.urls import path
from .views import ProductoListCreateView, ProductoDetailView, ProductoStockBodegasView

urlpatterns = [
    path('',                          ProductoListCreateView.as_view(),    name='producto-list'),
    path('<int:pk>/',                 ProductoDetailView.as_view(),        name='producto-detail'),
    path('<int:pk>/stock-bodegas/',   ProductoStockBodegasView.as_view(),  name='producto-stock-bodegas'),
]