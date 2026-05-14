from django.db import models
from proveedores.models import Proveedor
from productos.models import Producto
from users.models import Usuario


class Compra(models.Model):
    ESTADO_CHOICES = [
        ('Borrador',   'Borrador'),
        ('Enviada',    'Enviada'),
        ('Recibida',   'Recibida'),
        ('Cancelada',  'Cancelada'),
    ]
    CONDICION_PAGO_CHOICES = [
        ('Contado',   'Contado'),
        ('15_dias',   '15 días'),
        ('30_dias',   '30 días'),
        ('45_dias',   '45 días'),
        ('60_dias',   '60 días'),
        ('90_dias',   '90 días'),
    ]

    proveedor             = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='compras')
    total                 = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    estado                = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='Borrador')
    condicion_pago        = models.CharField(max_length=15, choices=CONDICION_PAGO_CHOICES, default='Contado')
    dias_credito          = models.PositiveIntegerField(default=0)
    fecha_vencimiento_pago= models.DateField(null=True, blank=True)
    notas                 = models.TextField(blank=True)
    creado_por            = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True,
                                              related_name='compras_creadas')
    fecha                 = models.DateField(auto_now_add=True)
    creado_en             = models.DateTimeField(auto_now_add=True)
    actualizado_en        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'compras'
        ordering = ['-fecha', '-id']
        verbose_name = 'Compra'

    def actualizar_total(self):
        total = sum(detalle.subtotal for detalle in self.detalles.all())
        self.total = total
        self.save(update_fields=['total'])

    def __str__(self):
        return f'OC-{self.id:04d} | {self.proveedor.razon_social}'


class DetalleCompra(models.Model):
    compra           = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto         = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_compra')
    cantidad         = models.PositiveIntegerField()
    precio_unitario  = models.DecimalField(max_digits=14, decimal_places=2)
    subtotal         = models.DecimalField(max_digits=16, decimal_places=2, editable=False)

    class Meta:
        db_table = 'detalle_compra'

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        self.compra.actualizar_total()

    def delete(self, *args, **kwargs):
        compra = self.compra
        super().delete(*args, **kwargs)
        compra.actualizar_total()

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'