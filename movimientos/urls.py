from django.urls import path
from .views import MovimientoListCreateView, MovimientoDetailView

urlpatterns = [
    path('',          MovimientoListCreateView.as_view(), name='movimiento-list'),
    path('<int:pk>/', MovimientoDetailView.as_view(),     name='movimiento-detail'),
]
