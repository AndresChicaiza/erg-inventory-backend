from django.db import models
from decimal import Decimal
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
    MONEDA_CHOICES = [
        ('COP', 'Pesos Colombianos'),
        ('USD', 'Dólares Estadounidenses'),
    ]

    proveedor             = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='compras')
    bodega_destino        = models.ForeignKey('bodegas.Bodega', on_delete=models.PROTECT, null=True, blank=True, help_text='Bodega donde ingresará la mercadería')
    
    # Valores
    moneda                = models.CharField(max_length=5, choices=MONEDA_CHOICES, default='COP')
    subtotal              = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    total_iva             = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    total                 = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    
    estado                = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='Borrador')
    condicion_pago        = models.CharField(max_length=15, choices=CONDICION_PAGO_CHOICES, default='Contado')
    dias_credito          = models.PositiveIntegerField(default=0)
    fecha_vencimiento_pago= models.DateField(null=True, blank=True)
    fecha_esperada_entrega= models.DateField(null=True, blank=True)
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
        subtotal = sum(detalle.subtotal for detalle in self.detalles.all())
        total_iva = sum(detalle.valor_iva for detalle in self.detalles.all())
        self.subtotal = subtotal
        self.total_iva = total_iva
        self.total = subtotal + total_iva
        self.save(update_fields=['subtotal', 'total_iva', 'total'])

    def __str__(self):
        return f'OC-{self.id:04d} | {self.proveedor.razon_social}'


class DetalleCompra(models.Model):
    compra           = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto         = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_compra')
    cantidad         = models.PositiveIntegerField()
    precio_unitario  = models.DecimalField(max_digits=14, decimal_places=2)
    porcentaje_iva   = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    valor_iva        = models.DecimalField(max_digits=16, decimal_places=2, default=0, editable=False)
    subtotal         = models.DecimalField(max_digits=16, decimal_places=2, editable=False)

    class Meta:
        db_table = 'detalle_compra'

    def save(self, *args, **kwargs):
        self.subtotal = Decimal(str(self.cantidad)) * Decimal(str(self.precio_unitario))
        self.valor_iva = self.subtotal * (Decimal(str(self.porcentaje_iva)) / Decimal('100'))
        super().save(*args, **kwargs)
        self.compra.actualizar_total()

    def delete(self, *args, **kwargs):
        compra = self.compra
        super().delete(*args, **kwargs)
        compra.actualizar_total()

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'


class NotaCreditoProveedor(models.Model):
    MOTIVO_CHOICES = [
        ('DEVOLUCION',  'Devolución de mercancía'),
        ('DESCUENTO',   'Descuento comercial'),
        ('ANULACION',   'Anulación de orden'),
        ('PRECIO',      'Ajuste de precio'),
        ('OTRO',        'Otro'),
    ]

    compra_original  = models.ForeignKey(Compra, on_delete=models.PROTECT, related_name='notas_credito')
    numero           = models.CharField(max_length=50, blank=True, help_text='Número de nota crédito del proveedor')
    motivo           = models.CharField(max_length=15, choices=MOTIVO_CHOICES)
    descripcion      = models.TextField()

    total            = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    creado_por       = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    creado_en        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table     = 'notas_credito_proveedor'
        ordering     = ['-creado_en']
        verbose_name = 'Nota Crédito Proveedor'

    def __str__(self):
        return f'NCP-{self.id} → {self.compra_original}'

    def recalcular_totales(self):
        self.total = sum(d.subtotal for d in self.detalles.all())
        self.save(update_fields=['total'])


class DetalleNotaCreditoProveedor(models.Model):
    nota_credito     = models.ForeignKey(NotaCreditoProveedor, on_delete=models.CASCADE, related_name='detalles')
    detalle_compra   = models.ForeignKey(DetalleCompra, on_delete=models.SET_NULL, null=True, blank=True, related_name='notas_credito_aplicadas')
    producto         = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True, blank=True)
    cantidad         = models.PositiveIntegerField()
    precio_unitario  = models.DecimalField(max_digits=14, decimal_places=2)
    subtotal         = models.DecimalField(max_digits=16, decimal_places=2, editable=False)

    class Meta:
        db_table  = 'nota_credito_proveedor_detalles'

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        nombre = self.producto.nombre if self.producto else 'Desconocido'
        return f'{self.cantidad} x {nombre}'