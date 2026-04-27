from django.contrib import admin
from .models import Proveedor

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display  = ('empresa', 'contacto', 'email', 'ciudad', 'categoria', 'tipo', 'estado')
    list_filter   = ('categoria', 'tipo', 'estado')
    search_fields = ('empresa', 'contacto', 'email')
