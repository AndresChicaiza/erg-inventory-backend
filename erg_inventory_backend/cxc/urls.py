from django.urls import path
from .views import CXCListCreateView, CXCDetailView, PagoCXCCreateView

urlpatterns = [
    path('',           CXCListCreateView.as_view(), name='cxc-list'),
    path('<int:pk>/',  CXCDetailView.as_view(),     name='cxc-detail'),
    path('pagos/',     PagoCXCCreateView.as_view(),  name='pago-cxc'),
]
