from django.urls import path
from .views import (
    RecetaListCreateView, RecetaDetailView,
    IngredienteRecetaListCreateView, IngredienteRecetaDetailView,
    OrdenProduccionListCreateView, OrdenProduccionDetailView,
    CompletarOrdenProduccionView
)

urlpatterns = [
    path('recetas/', RecetaListCreateView.as_view(), name='receta-list'),
    path('recetas/<int:pk>/', RecetaDetailView.as_view(), name='receta-detail'),
    path('recetas/<int:receta_id>/ingredientes/', IngredienteRecetaListCreateView.as_view(), name='ingrediente-list'),
    path('ingredientes/<int:pk>/', IngredienteRecetaDetailView.as_view(), name='ingrediente-detail'),
    
    path('ordenes/', OrdenProduccionListCreateView.as_view(), name='orden-list'),
    path('ordenes/<int:pk>/', OrdenProduccionDetailView.as_view(), name='orden-detail'),
    path('ordenes/<int:pk>/completar/', CompletarOrdenProduccionView.as_view(), name='orden-completar'),
]
