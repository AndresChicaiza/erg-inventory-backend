# ── configuracion/urls.py ─────────────────────────────────────────────────────
from django.urls import path
from .views import (
    ConfiguracionView,
    TarifaRetefuenteListView,
    TarifaReteICAListView,
)

urlpatterns = [
    path('configuracion/',                    ConfiguracionView.as_view(),          name='configuracion'),
    path('configuracion/tarifas-retefuente/', TarifaRetefuenteListView.as_view(),   name='tarifas-retefuente'),
    path('configuracion/tarifas-reteica/',    TarifaReteICAListView.as_view(),      name='tarifas-reteica'),
]


# ── configuracion/apps.py ─────────────────────────────────────────────────────
# (contenido para apps.py — crear archivo separado si es necesario)
"""
from django.apps import AppConfig

class ConfiguracionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'configuracion'
    verbose_name       = 'Configuración'
"""