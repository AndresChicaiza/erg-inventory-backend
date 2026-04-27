from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'email', 'telefono', 'tipo', 'ciudad', 'estado')
    list_filter   = ('tipo', 'estado')
    search_fields = ('nombre', 'email')
