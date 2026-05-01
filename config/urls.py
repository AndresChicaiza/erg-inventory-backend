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
        path('', include('clientes.urls')),
        path('', include('proveedores.urls')),

        # ── Inventario ────────────────────────────────────────────
        path('', include('productos.urls')),
        path('', include('bodegas.urls')),
        path('', include('movimientos.urls')),
        path('', include('kardex.urls')),

        # ── Ventas y Facturas ─────────────────────────────────────
        path('', include('ventas.urls')),
        path('', include('compras.urls')),
        path('', include('entregas.urls')),

        # ── Finanzas ──────────────────────────────────────────────
        path('', include('cxc.urls')),
        path('', include('cxp.urls')),

        # ── RRHH ──────────────────────────────────────────────────
        path('', include('nomina.urls')),

        # ── Reportes ──────────────────────────────────────────────
        path('', include('reportes.urls')),
    ])),
]

# Servir archivos de media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)