from django.contrib import admin
from .models import Bodega, StockBodega

@admin.register(Bodega)
class BodegaAdmin(admin.ModelAdmin):
    list_display  = ('codigo', 'nombre', 'ciudad', 'responsable', 'estado')
    list_filter   = ('estado',)
    search_fields = ('nombre', 'codigo')

@admin.register(StockBodega)
class StockBodegaAdmin(admin.ModelAdmin):
    list_display  = ('bodega', 'producto', 'cantidad')
    list_filter   = ('bodega',)
