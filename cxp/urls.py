from django.urls import path
from .views import (
    CXPListCreateView, CXPDetailView,
    PagoCXPCreateView, CXPResumenView, CXPPorProveedorView, AnularCXPView
)
from .views_exogena import Exogena1009View

urlpatterns = [
    path('',                 CXPListCreateView.as_view(),    name='cxp-list'),
    path('<int:pk>/',        CXPDetailView.as_view(),        name='cxp-detail'),
    path('<int:pk>/anular/', AnularCXPView.as_view(),        name='cxp-anular'),
    path('pagos/',           PagoCXPCreateView.as_view(),    name='cxp-pagos'),
    path('resumen/',         CXPResumenView.as_view(),       name='cxp-resumen'),
    path('por-proveedor/',   CXPPorProveedorView.as_view(),  name='cxp-por-proveedor'),
    path('exogena/1009/',    Exogena1009View.as_view(),      name='exogena-1009'),
]