from django.db import models
from proveedores.models import Proveedor
from productos.models import Producto
from users.models import Usuario


class Compra(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente',  'Pendiente'),
        ('Recibida',   'Recibida'),
        ('Cancelada',  'Cancelada'),
    ]

    proveedor        = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='compras')
    producto         = models.ForeignKey(Producto,  on_delete=models.PROTECT, related_name='compras')
    cantidad         = models.PositiveIntegerField()
    precio_unitario  = models.DecimalField(max_digits=14, decimal_places=2)
    total            = models.DecimalField(max_digits=16, decimal_places=2, editable=False)
    estado           = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Pendiente')
    notas            = models.TextField(blank=True)
    creado_por       = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True,
                                         related_name='compras_creadas')
    fecha            = models.DateField(auto_now_add=True)
    creado_en        = models.DateTimeField(auto_now_add=True)
    actualizado_en   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compras'
        ordering = ['-fecha', '-id']
        verbose_name = 'Compra'

    def save(self, *args, **kwargs):
        self.total = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f'OC-{self.id:04d} | {self.proveedor.empresa}'
