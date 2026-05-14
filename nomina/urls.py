from django.urls import path
from .views import (
    EmpleadoListCreateView, EmpleadoDetailView,
    PeriodoNominaListCreateView, PeriodoNominaDetailView,
    LineaNominaListCreateView, LineaNominaDetailView,
    CerrarPeriodoView, ConceptoNominaListView,
)

urlpatterns = [
    # Empleados
    path('empleados/',           EmpleadoListCreateView.as_view(), name='empleado-list'),
    path('empleados/<int:pk>/',  EmpleadoDetailView.as_view(),     name='empleado-detail'),
    # Períodos
    path('periodos/',                    PeriodoNominaListCreateView.as_view(), name='periodo-list'),
    path('periodos/<int:pk>/',           PeriodoNominaDetailView.as_view(),     name='periodo-detail'),
    path('periodos/<int:pk>/cerrar/',    CerrarPeriodoView.as_view(),           name='periodo-cerrar'),
    # Líneas
    path('lineas/',              LineaNominaListCreateView.as_view(), name='linea-list'),
    path('lineas/<int:pk>/',     LineaNominaDetailView.as_view(),    name='linea-detail'),
    # Conceptos
    path('conceptos/',           ConceptoNominaListView.as_view(),   name='concepto-list'),
]
