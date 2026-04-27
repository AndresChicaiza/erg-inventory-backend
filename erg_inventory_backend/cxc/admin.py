from django.contrib import admin
from .models import CuentaPorCobrar, PagoCXC

@admin.register(CuentaPorCobrar)
class CXCAdmin(admin.ModelAdmin):
    list_display  = ('id', 'cliente', 'concepto', 'monto_total', 'saldo', 'estado', 'fecha_vencimiento')
    list_filter   = ('estado',)
    search_fields = ('cliente__nombre', 'concepto')
    readonly_fields = ('saldo',)

admin.site.register(PagoCXC)
