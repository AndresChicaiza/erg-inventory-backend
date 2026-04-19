from django.urls import path
from .views import EntregaListCreateView, EntregaDetailView

urlpatterns = [
    path('',          EntregaListCreateView.as_view(), name='entrega-list'),
    path('<int:pk>/', EntregaDetailView.as_view(),     name='entrega-detail'),
]
