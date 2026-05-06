from django.urls import path
from .views import (
    CXPListCreateView, CXPDetailView,
    PagoCXPCreateView, CXPResumenView, CXPPorProveedorView
)

urlpatterns = [
    path('cxp/',                 CXPListCreateView.as_view(),    name='cxp-list'),
    path('cxp/<int:pk>/',        CXPDetailView.as_view(),        name='cxp-detail'),
    path('cxp/pagos/',           PagoCXPCreateView.as_view(),    name='cxp-pagos'),
    path('cxp/resumen/',         CXPResumenView.as_view(),       name='cxp-resumen'),
    path('cxp/por-proveedor/',   CXPPorProveedorView.as_view(),  name='cxp-por-proveedor'),
]