from django.urls import path
from .views import KardexListView, KardexProductosView

urlpatterns = [
    path('',          KardexListView.as_view(),     name='kardex-list'),
    path('productos/', KardexProductosView.as_view(), name='kardex-productos'),
]
