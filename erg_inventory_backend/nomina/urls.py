from django.urls import path
from .views import (PeriodoNominaListCreateView, PeriodoNominaDetailView,
                    LineaNominaListCreateView, LineaNominaDetailView,
                    CerrarPeriodoView, ConceptoNominaListView)

urlpatterns = [
    path('periodos/',              PeriodoNominaListCreateView.as_view(), name='periodo-list'),
    path('periodos/<int:pk>/',     PeriodoNominaDetailView.as_view(),     name='periodo-detail'),
    path('periodos/<int:pk>/cerrar/', CerrarPeriodoView.as_view(),        name='periodo-cerrar'),
    path('lineas/',                LineaNominaListCreateView.as_view(),   name='linea-list'),
    path('lineas/<int:pk>/',       LineaNominaDetailView.as_view(),       name='linea-detail'),
    path('conceptos/',             ConceptoNominaListView.as_view(),      name='concepto-list'),
]
