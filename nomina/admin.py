from django.contrib import admin
from .models import Empleado, PeriodoNomina, LineaNomina, ConceptoNomina


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display  = ('nombre', 'numero_documento', 'cargo', 'tipo_contrato', 'salario_base', 'estado')
    list_filter   = ('estado', 'tipo_contrato')
    search_fields = ('nombre', 'numero_documento', 'cargo')


@admin.register(PeriodoNomina)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin', 'estado', 'total_neto')


@admin.register(LineaNomina)
class LineaAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'periodo', 'salario_base', 'total_devengado', 'total_deducciones', 'neto_pagar')


admin.site.register(ConceptoNomina)
