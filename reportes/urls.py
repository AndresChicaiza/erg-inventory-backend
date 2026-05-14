from django.urls import path
from .views import ResumenView, FlujoCajaView

urlpatterns = [
    path('resumen/',    ResumenView.as_view(),    name='reportes-resumen'),
    path('flujo-caja/', FlujoCajaView.as_view(),  name='reportes-flujo-caja'),
]
