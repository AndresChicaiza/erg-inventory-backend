from django.contrib import admin
from .models import CuentaPorPagar, PagoCXP

@admin.register(CuentaPorPagar)
class CXPAdmin(admin.ModelAdmin):
    list_display  = ('id', 'proveedor', 'concepto', 'monto_total', 'saldo', 'estado', 'fecha_vencimiento')
    list_filter   = ('estado',)
    search_fields = ('proveedor__empresa', 'concepto')
    readonly_fields = ('saldo',)

admin.site.register(PagoCXP)
