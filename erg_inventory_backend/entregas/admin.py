from django.contrib import admin
from .models import Entrega

@admin.register(Entrega)
class EntregaAdmin(admin.ModelAdmin):
    list_display  = ('id', 'cliente', 'transportista', 'estado', 'fecha_estimada')
    list_filter   = ('estado',)
    search_fields = ('cliente__nombre', 'transportista')
