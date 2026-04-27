from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display  = ('codigo', 'nombre', 'categoria', 'precio_venta', 'stock', 'estado')
    list_filter   = ('categoria', 'estado')
    search_fields = ('codigo', 'nombre')
    ordering      = ('nombre',)
