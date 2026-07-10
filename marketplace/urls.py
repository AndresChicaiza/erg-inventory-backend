from django.urls import path
from . import views

urlpatterns = [

    # ── Endpoints PÚBLICOS (portal B2B, sin autenticación) ───────────────────
    path('catalogo/',                     views.CatalogoPublicoListView.as_view(), name='mktpl-catalogo-publico'),
    path('pedidos/',                      views.PedidoCreateView.as_view(),        name='mktpl-pedido-crear'),
    path('pedidos/estado/<str:token>/',   views.PedidoStatusView.as_view(),        name='mktpl-pedido-estado'),

    # ── Endpoints ADMIN (panel ERP, requieren autenticación) ─────────────────
    path('admin/resumen/',                views.ResumenMarketplaceView.as_view(),   name='mktpl-resumen'),

    # Pedidos
    path('admin/pedidos/',                views.PedidoAdminListView.as_view(),      name='mktpl-admin-pedidos'),
    path('admin/pedidos/<int:pk>/',       views.PedidoAdminDetailView.as_view(),    name='mktpl-admin-pedido-detail'),
    path('admin/pedidos/<int:pk>/aprobar/',  views.PedidoAprobarView.as_view(),     name='mktpl-pedido-aprobar'),
    path('admin/pedidos/<int:pk>/rechazar/', views.PedidoRechazarView.as_view(),    name='mktpl-pedido-rechazar'),

    # Catálogo
    path('admin/catalogo/',               views.CatalogoAdminListView.as_view(),    name='mktpl-admin-catalogo'),
    path('admin/catalogo/<int:pk>/',      views.CatalogoAdminDetailView.as_view(),  name='mktpl-admin-catalogo-detail'),
    path('admin/catalogo/<int:pk>/toggle/', views.ToggleVisibilidadView.as_view(),  name='mktpl-catalogo-toggle'),
]
