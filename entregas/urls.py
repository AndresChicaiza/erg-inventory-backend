from django.urls import path
from .views import EntregaListCreateView, EntregaDetailView, RecibirTrasladoView

urlpatterns = [
    path('',          EntregaListCreateView.as_view(), name='entrega-list'),
    path('<int:pk>/', EntregaDetailView.as_view(),     name='entrega-detail'),
    path('<int:pk>/recibir/', RecibirTrasladoView.as_view(), name='entrega-recibir'),
]
