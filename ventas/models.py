from django.db import models
from clientes.models import Cliente
from productos.models import Producto
from users.models import Usuario


class Venta(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente',  'Pendiente'),
        ('Pagada',     'Pagada'),
        ('Cancelada',  'Cancelada'),
    ]

    cliente          = models.ForeignKey(Cliente,  on_delete=models.PROTECT, related_name='ventas')
    producto         = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='ventas')
    # Bodega desde la que sale el producto (opcional — si no se elige, solo descuenta stock global)
    bodega           = models.ForeignKey(
                           'bodegas.Bodega',
                           on_delete=models.SET_NULL,
                           null=True, blank=True,
                           related_name='ventas'
                       )
    cantidad         = models.PositiveIntegerField()
    precio_unitario  = models.DecimalField(max_digits=14, decimal_places=2)
    total            = models.DecimalField(max_digits=16, decimal_places=2, editable=False)
    estado           = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Pendiente')
    notas            = models.TextField(blank=True)
    creado_por       = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True,
                                         related_name='ventas_creadas')
    fecha            = models.DateField(auto_now_add=True)
    creado_en        = models.DateTimeField(auto_now_add=True)
    actualizado_en   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table   = 'ventas'
        ordering   = ['-fecha', '-id']
        verbose_name = 'Venta'

    def save(self, *args, **kwargs):
        self.total = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f'V-{self.id:04d} | {self.cliente.nombre}'