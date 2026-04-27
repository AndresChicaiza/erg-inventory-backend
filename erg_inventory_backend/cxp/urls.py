from django.urls import path
from .views import CXPListCreateView, CXPDetailView, PagoCXPCreateView

urlpatterns = [
    path('',          CXPListCreateView.as_view(), name='cxp-list'),
    path('<int:pk>/', CXPDetailView.as_view(),     name='cxp-detail'),
    path('pagos/',    PagoCXPCreateView.as_view(),  name='pago-cxp'),
]
