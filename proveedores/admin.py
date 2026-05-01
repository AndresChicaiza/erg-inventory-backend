from django.contrib import admin
from .models import Proveedor


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display  = ('razon_social', 'tipo_documento', 'numero_documento', 'contacto', 'ciudad', 'categoria', 'estado')
    list_filter   = ('tipo_documento', 'categoria', 'regimen_tributario', 'estado')
    search_fields = ('razon_social', 'numero_documento', 'contacto', 'email')