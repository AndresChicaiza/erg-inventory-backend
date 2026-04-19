from django.urls import path
from .views import CompraListCreateView, CompraDetailView

urlpatterns = [
    path('',          CompraListCreateView.as_view(), name='compra-list'),
    path('<int:pk>/', CompraDetailView.as_view(),     name='compra-detail'),
]
