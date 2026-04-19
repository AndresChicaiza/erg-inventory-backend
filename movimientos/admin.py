from django.contrib import admin
from .models import Movimiento

@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display  = ('id', 'producto', 'tipo', 'cantidad', 'referencia', 'creado_por', 'fecha')
    list_filter   = ('tipo', 'fecha')
    search_fields = ('producto__nombre', 'referencia')
    readonly_fields = ('fecha', 'creado_en')
