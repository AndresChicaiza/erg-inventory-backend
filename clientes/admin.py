from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display  = ('razon_social', 'tipo_documento', 'numero_documento', 'ciudad', 'regimen_tributario', 'estado')
    list_filter   = ('tipo_documento', 'regimen_tributario', 'estado', 'responsable_iva')
    search_fields = ('razon_social', 'numero_documento', 'email')