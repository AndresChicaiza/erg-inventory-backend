from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    # Auth
    path('api/auth/login/',   include('users.urls_auth')),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/me/',      include('users.urls_me')),
    # Módulos originales
    path('api/usuarios/',    include('users.urls')),
    path('api/productos/',   include('productos.urls')),
    path('api/clientes/',    include('clientes.urls')),
    path('api/proveedores/', include('proveedores.urls')),
    path('api/ventas/',      include('ventas.urls')),
    path('api/compras/',     include('compras.urls')),
    path('api/entregas/',    include('entregas.urls')),
    path('api/movimientos/', include('movimientos.urls')),
    path('api/kardex/',      include('kardex.urls')),
    path('api/reportes/',    include('reportes.urls')),
    # Nuevos módulos
    path('api/bodegas/',     include('bodegas.urls')),
    path('api/cxc/',         include('cxc.urls')),
    path('api/cxp/',         include('cxp.urls')),
    path('api/nomina/',      include('nomina.urls')),
]
