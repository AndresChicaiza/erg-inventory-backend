from django.contrib import admin
from .models import Compra

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display  = ('id', 'proveedor', 'producto', 'cantidad', 'total', 'estado', 'fecha')
    list_filter   = ('estado', 'fecha')
    search_fields = ('proveedor__empresa', 'producto__nombre')
    readonly_fields = ('total',)
