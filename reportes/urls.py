from django.urls import path
from .views import (
    ResumenView, AlertasView, FlujoCajaView,
    ExportarNominaView, ExportarCXCView, ExportarCXPView,
)

urlpatterns = [
    path('resumen/',                      ResumenView.as_view(),         name='reportes-resumen'),
    path('alertas/',                      AlertasView.as_view(),         name='reportes-alertas'),
    path('flujo-caja/',                   FlujoCajaView.as_view(),       name='reportes-flujo-caja'),
    # Exportaciones PDF
    path('exportar/nomina/<int:periodo_id>/', ExportarNominaView.as_view(), name='exportar-nomina'),
    path('exportar/cxc/',                 ExportarCXCView.as_view(),     name='exportar-cxc'),
    path('exportar/cxp/',                 ExportarCXPView.as_view(),     name='exportar-cxp'),
]
