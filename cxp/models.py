from django.db import models
from proveedores.models import Proveedor
from compras.models import Compra
from users.models import Usuario


class CuentaPorPagar(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Parcial',   'Parcial'),
        ('Pagada',    'Pagada'),
        ('Vencida',   'Vencida'),
        ('Anulada',   'Anulada'),
    ]

    proveedor      = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='cxp')
    compra         = models.OneToOneField(Compra, on_delete=models.SET_NULL, null=True, blank=True, related_name='cxp')
    concepto       = models.CharField(max_length=255)
    monto_total    = models.DecimalField(max_digits=16, decimal_places=2)
    monto_pagado   = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    saldo          = models.DecimalField(max_digits=16, decimal_places=2, editable=False)
    fecha_emision  = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    estado         = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Pendiente')
    notas          = models.TextField(blank=True)
    creado_por     = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='cxp_creadas')
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table   = 'cuentas_por_pagar'
        ordering   = ['-fecha_emision']
        verbose_name = 'Cuenta por Pagar'

    def save(self, *args, **kwargs):
        self.saldo = self.monto_total - self.monto_pagado
        if self.saldo <= 0:
            self.estado = 'Pagada'
        elif self.monto_pagado > 0:
            self.estado = 'Parcial'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'CXP-{self.id:04d} | {self.proveedor.empresa} | {self.estado}'


class PagoCXP(models.Model):
    METODO_CHOICES = [
        ('Efectivo',      'Efectivo'),
        ('Transferencia', 'Transferencia'),
        ('Tarjeta',       'Tarjeta'),
        ('Cheque',        'Cheque'),
    ]
    cxp        = models.ForeignKey(CuentaPorPagar, on_delete=models.CASCADE, related_name='pagos')
    monto      = models.DecimalField(max_digits=16, decimal_places=2)
    metodo     = models.CharField(max_length=15, choices=METODO_CHOICES, default='Transferencia')
    referencia = models.CharField(max_length=100, blank=True)
    fecha      = models.DateField(auto_now_add=True)
    notas      = models.TextField(blank=True)
    creado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    creado_en  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pagos_cxp'
        ordering = ['-fecha']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from django.db.models import Sum
        total = self.cxp.pagos.aggregate(t=Sum('monto'))['t'] or 0
        self.cxp.monto_pagado = total
        self.cxp.save()
