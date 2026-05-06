from django.urls import path
from .views import CXCListCreateView, CXCDetailView, PagoCXCCreateView, CXCResumenView

urlpatterns = [
    path('cxc/',              CXCListCreateView.as_view(), name='cxc-list'),
    path('cxc/<int:pk>/',     CXCDetailView.as_view(),    name='cxc-detail'),
    path('cxc/pagos/',        PagoCXCCreateView.as_view(), name='cxc-pagos'),
    path('cxc/resumen/',      CXCResumenView.as_view(),    name='cxc-resumen'),
]