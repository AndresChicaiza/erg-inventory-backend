from django.urls import path
from .views import ProductoListCreateView, ProductoDetailView, ProductoStockBodegasView, LoteListView

urlpatterns = [
    path('',                          ProductoListCreateView.as_view(),    name='producto-list'),
    path('<int:pk>/',                 ProductoDetailView.as_view(),        name='producto-detail'),
    path('<int:pk>/stock-bodegas/',   ProductoStockBodegasView.as_view(),  name='producto-stock-bodegas'),
    path('<int:pk>/lotes/',           LoteListView.as_view(),              name='producto-lotes'),
]