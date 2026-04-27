from django.contrib import admin
from .models import PeriodoNomina, LineaNomina, ConceptoNomina

@admin.register(PeriodoNomina)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin', 'estado', 'total_neto')

@admin.register(LineaNomina)
class LineaAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'periodo', 'salario_base', 'total_devengado', 'total_deducciones', 'neto_pagar')

admin.site.register(ConceptoNomina)
