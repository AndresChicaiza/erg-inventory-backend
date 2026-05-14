from django.urls import path
from .views import ClienteListCreateView, ClienteDetailView, ClienteImportView

urlpatterns = [
    path('',          ClienteListCreateView.as_view(), name='cliente-list'),
    path('importar/', ClienteImportView.as_view(),     name='cliente-importar'),
    path('<int:pk>/', ClienteDetailView.as_view(),     name='cliente-detail'),
]
