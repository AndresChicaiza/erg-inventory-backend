from django.db import models
from users.models import Usuario


class ConceptoNomina(models.Model):
    """Devengados y deducciones."""
    TIPO_CHOICES = [('Devengado', 'Devengado'), ('Deduccion', 'Deducción')]
    nombre      = models.CharField(max_length=150)
    tipo        = models.CharField(max_length=10, choices=TIPO_CHOICES)
    porcentaje  = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text='0 si es valor fijo')
    activo      = models.BooleanField(default=True)

    class Meta:
        db_table = 'conceptos_nomina'
        verbose_name = 'Concepto de Nómina'

    def __str__(self):
        return f'{self.nombre} ({self.tipo})'


class PeriodoNomina(models.Model):
    ESTADO_CHOICES = [('Borrador', 'Borrador'), ('Aprobada', 'Aprobada'), ('Pagada', 'Pagada')]
    nombre        = models.CharField(max_length=100)
    fecha_inicio  = models.DateField()
    fecha_fin     = models.DateField()
    estado        = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Borrador')
    total_devengado  = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    total_deducciones = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    total_neto       = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    creado_por    = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='periodos_nomina')
    creado_en     = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'periodos_nomina'
        ordering = ['-fecha_inicio']
        verbose_name = 'Período de Nómina'

    def __str__(self):
        return f'{self.nombre} | {self.estado}'


class LineaNomina(models.Model):
    """Detalle por empleado en un período."""
    periodo        = models.ForeignKey(PeriodoNomina, on_delete=models.CASCADE, related_name='lineas')
    empleado       = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='nominas')
    salario_base   = models.DecimalField(max_digits=14, decimal_places=2)
    dias_trabajados = models.IntegerField(default=30)
    # Devengados
    auxilio_transporte = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    horas_extra    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonificaciones = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_devengado = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # Deducciones
    salud          = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # 4%
    pension        = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # 4%
    retencion_fuente = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    otras_deducciones = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_deducciones = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    # Neto
    neto_pagar     = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notas          = models.TextField(blank=True)

    class Meta:
        db_table   = 'lineas_nomina'
        unique_together = ('periodo', 'empleado')
        verbose_name = 'Línea de Nómina'

    def save(self, *args, **kwargs):
        self.total_devengado  = self.salario_base + self.auxilio_transporte + self.horas_extra + self.bonificaciones
        self.salud            = self.salario_base * 4 / 100
        self.pension          = self.salario_base * 4 / 100
        self.total_deducciones = self.salud + self.pension + self.retencion_fuente + self.otras_deducciones
        self.neto_pagar       = self.total_devengado - self.total_deducciones
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.empleado.nombre} | {self.periodo.nombre} | {self.neto_pagar}'
