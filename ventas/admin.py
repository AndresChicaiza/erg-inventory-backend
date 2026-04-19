from django.contrib import admin
from .models import Venta

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display  = ('id', 'cliente', 'producto', 'cantidad', 'total', 'estado', 'fecha')
    list_filter   = ('estado', 'fecha')
    search_fields = ('cliente__nombre', 'producto__nombre')
    readonly_fields = ('total',)
