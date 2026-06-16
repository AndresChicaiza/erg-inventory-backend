from django.urls import path
from .views import (
    FacturaListCreateView, FacturaDetailView,
    DetalleFacturaListCreateView, DetalleFacturaDetailView,
    EmitirFacturaView, AnularFacturaView, MarcarFacturaPagadaView,
    CalcularImpuestosView, FacturaPDFView,
    ResumenFacturacionView,
    NotaCreditoListCreateView, NotaCreditoDetailView,
    EmitirDianView, ConsultarEstadoDianView,
)

urlpatterns = [
    # Facturas
    path('facturas/',                          FacturaListCreateView.as_view(),       name='factura-list'),
    path('facturas/resumen/',                  ResumenFacturacionView.as_view(),       name='factura-resumen'),
    path('facturas/calcular-impuestos/',       CalcularImpuestosView.as_view(),        name='factura-calcular'),
    path('facturas/<int:pk>/',                 FacturaDetailView.as_view(),            name='factura-detail'),
    path('facturas/<int:pk>/emitir/',          EmitirFacturaView.as_view(),            name='factura-emitir'),
    path('facturas/<int:pk>/anular/',          AnularFacturaView.as_view(),            name='factura-anular'),
    path('facturas/<int:pk>/pagar/',           MarcarFacturaPagadaView.as_view(),      name='factura-pagar'),
    path('facturas/<int:pk>/pdf/',             FacturaPDFView.as_view(),               name='factura-pdf'),
    path('facturas/<int:pk>/emitir-dian/',     EmitirDianView.as_view(),               name='factura-emitir-dian'),
    path('facturas/<int:pk>/estado-dian/',     ConsultarEstadoDianView.as_view(),      name='factura-estado-dian'),

    # Detalles (ítems) de factura
    path('facturas/<int:factura_id>/detalles/',       DetalleFacturaListCreateView.as_view(), name='detalle-list'),
    path('facturas/detalles/<int:pk>/',               DetalleFacturaDetailView.as_view(),     name='detalle-detail'),

    # Notas crédito
    path('notas-credito/',                     NotaCreditoListCreateView.as_view(),    name='nota-credito-list'),
    path('notas-credito/<int:pk>/',            NotaCreditoDetailView.as_view(),        name='nota-credito-detail'),
]