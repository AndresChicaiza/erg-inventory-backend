from django.contrib import admin
from .models import CatalogoPublico, PedidoOnline, DetallePedidoOnline


class DetallePedidoInline(admin.TabularInline):
    model  = DetallePedidoOnline
    extra  = 0
    fields = ['nombre_producto', 'cantidad', 'precio_unitario', 'subtotal_linea']
    readonly_fields = ['subtotal_linea']


@admin.register(CatalogoPublico)
class CatalogoPublicoAdmin(admin.ModelAdmin):
    list_display  = ['producto', 'visible', 'precio_publico', 'precio_efectivo', 'orden']
    list_filter   = ['visible']
    search_fields = ['producto__nombre', 'producto__codigo']
    list_editable = ['visible', 'orden']


@admin.register(PedidoOnline)
class PedidoOnlineAdmin(admin.ModelAdmin):
    list_display  = ['pk', 'cliente_nombre', 'cliente_email', 'total', 'estado', 'creado_en']
    list_filter   = ['estado']
    search_fields = ['cliente_nombre', 'cliente_email', 'cliente_nit', 'token']
    readonly_fields = ['token', 'creado_en', 'actualizado_en', 'revisado_en']
    inlines       = [DetallePedidoInline]
