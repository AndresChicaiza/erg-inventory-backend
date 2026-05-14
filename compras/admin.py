from django.contrib import admin
from .models import Compra, DetalleCompra

class DetalleCompraInline(admin.TabularInline):
    model = DetalleCompra
    extra = 1
    readonly_fields = ('subtotal',)

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display  = ('id', 'proveedor', 'total', 'estado', 'fecha')
    list_filter   = ('estado', 'fecha')
    search_fields = ('proveedor__razon_social',)
    readonly_fields = ('total',)
    inlines = [DetalleCompraInline]
