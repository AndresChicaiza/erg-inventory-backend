from django.urls import path
from .views import CXCListCreateView, CXCDetailView, PagoCXCCreateView, CXCResumenView, AnularCXCView
from .views_exogena import Exogena1008View

urlpatterns = [
    path('',              CXCListCreateView.as_view(), name='cxc-list'),
    path('<int:pk>/',     CXCDetailView.as_view(),    name='cxc-detail'),
    path('<int:pk>/anular/', AnularCXCView.as_view(),  name='cxc-anular'),
    path('pagos/',        PagoCXCCreateView.as_view(), name='cxc-pagos'),
    path('resumen/',      CXCResumenView.as_view(),    name='cxc-resumen'),
    path('exogena/1008/', Exogena1008View.as_view(),   name='exogena-1008'),
]