from django.db import models
from django.utils import timezone
from clientes.models import Cliente
from ventas.models import Venta
from users.models import Usuario


class CuentaPorCobrar(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Parcial',   'Parcial'),
        ('Pagada',    'Pagada'),
        ('Vencida',   'Vencida'),
        ('Anulada',   'Anulada'),
    ]

    cliente           = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='cxc')
    venta             = models.OneToOneField(Venta, on_delete=models.SET_NULL,
                            null=True, blank=True, related_name='cxc')
    concepto          = models.CharField(max_length=255)
    monto_total       = models.DecimalField(max_digits=16, decimal_places=2)
    monto_pagado      = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    saldo             = models.DecimalField(max_digits=16, decimal_places=2, editable=False)
    fecha_emision     = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    estado            = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Pendiente')
    notas             = models.TextField(blank=True)
    creado_por        = models.ForeignKey(Usuario, on_delete=models.SET_NULL,
                            null=True, related_name='cxc_creadas')
    creado_en         = models.DateTimeField(auto_now_add=True)
    actualizado_en    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table   = 'cuentas_por_cobrar'
        ordering   = ['-fecha_emision']
        verbose_name = 'Cuenta por Cobrar'

    def save(self, *args, **kwargs):
        self.saldo = self.monto_total - self.monto_pagado
        # No tocar si está anulada
        if self.estado != 'Anulada':
            if self.saldo <= 0:
                self.estado = 'Pagada'
            elif self.monto_pagado > 0:
                self.estado = 'Parcial'
            elif self.fecha_vencimiento and self.fecha_vencimiento < timezone.now().date():
                self.estado = 'Vencida'
            else:
                self.estado = 'Pendiente'
        super().save(*args, **kwargs)

    def __str__(self):
        # ✅ Fix: usa razon_social en lugar de nombre
        return f'CXC-{self.id:04d} | {self.cliente.razon_social} | {self.estado}'

    @property
    def dias_vencimiento(self):
        """Retorna los días para vencer (negativo = ya venció)."""
        delta = self.fecha_vencimiento - timezone.now().date()
        return delta.days

    @property
    def alerta_vencimiento(self):
        """Retorna el tipo de alerta según proximidad de vencimiento."""
        dias = self.dias_vencimiento
        if self.estado in ('Pagada', 'Anulada'):
            return None
        if dias < 0:
            return 'vencida'
        if dias <= 7:
            return 'proxima'
        return None


class PagoCXC(models.Model):
    METODO_CHOICES = [
        ('Efectivo',      'Efectivo'),
        ('Transferencia', 'Transferencia'),
        ('Tarjeta',       'Tarjeta'),
        ('Cheque',        'Cheque'),
    ]
    cxc        = models.ForeignKey(CuentaPorCobrar, on_delete=models.CASCADE, related_name='pagos')
    monto      = models.DecimalField(max_digits=16, decimal_places=2)
    metodo     = models.CharField(max_length=15, choices=METODO_CHOICES, default='Efectivo')
    referencia = models.CharField(max_length=100, blank=True)
    fecha      = models.DateField(auto_now_add=True)
    notas      = models.TextField(blank=True)
    creado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    creado_en  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pagos_cxc'
        ordering = ['-fecha']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from django.db.models import Sum
        total = self.cxc.pagos.aggregate(t=Sum('monto'))['t'] or 0
        self.cxc.monto_pagado = total
        self.cxc.save()

    def __str__(self):
        return f'Pago CXC-{self.cxc_id:04d} | ${self.monto}'