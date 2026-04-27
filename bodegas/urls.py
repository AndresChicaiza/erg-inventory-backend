from django.urls import path
from .views import BodegaListCreateView, BodegaDetailView, StockBodegaListView, TransferirStockView

urlpatterns = [
    path('',            BodegaListCreateView.as_view(), name='bodega-list'),
    path('<int:pk>/',   BodegaDetailView.as_view(),     name='bodega-detail'),
    path('stock/',      StockBodegaListView.as_view(),  name='stock-bodega'),
    path('transferir/', TransferirStockView.as_view(),  name='transferir-stock'),
]
