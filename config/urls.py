from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/', include([
        # ── Auth JWT ──────────────────────────────────────────────
        path('auth/login/',   TokenObtainPairView.as_view(),  name='token_obtain'),
        path('auth/refresh/', TokenRefreshView.as_view(),     name='token_refresh'),

        # ── Users y Sedes ─────────────────────────────────────────
        path('', include('users.urls')),

        # ── Configuración empresa y tarifas ───────────────────────
        path('', include('configuracion.urls')),

        # ── Clientes y Proveedores ────────────────────────────────
        path('clientes/', include('clientes.urls')),
        path('proveedores/', include('proveedores.urls')),

        # ── Inventario ────────────────────────────────────────────
        path('productos/', include('productos.urls')),
        path('bodegas/', include('bodegas.urls')),
        path('movimientos/', include('movimientos.urls')),
        path('kardex/', include('kardex.urls')),

        # ── Ventas y Facturas ─────────────────────────────────────
        path('ventas/', include('ventas.urls')),
        path('compras/', include('compras.urls')),
        path('entregas/', include('entregas.urls')),

        # ── Finanzas ──────────────────────────────────────────────
        path('cxc/', include('cxc.urls')),
        path('cxp/', include('cxp.urls')),

        # ── RRHH ──────────────────────────────────────────────────
        path('nomina/', include('nomina.urls')),

        # ── Reportes ──────────────────────────────────────────────
        path('reportes/', include('reportes.urls')),
    ])),
]

# Servir archivos de media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)