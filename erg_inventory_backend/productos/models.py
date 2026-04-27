from django.db import models


class Producto(models.Model):
    ESTADO_CHOICES = [('Activo', 'Activo'), ('Inactivo', 'Inactivo')]

    codigo       = models.CharField(max_length=30, unique=True)
    nombre       = models.CharField(max_length=200)
    descripcion  = models.TextField(blank=True)
    categoria    = models.CharField(max_length=100)
    precio_venta = models.DecimalField(max_digits=14, decimal_places=2)
    precio_costo = models.DecimalField(max_digits=14, decimal_places=2)
    stock        = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)
    estado       = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Activo')
    creado_en    = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table   = 'productos'
        ordering   = ['nombre']
        verbose_name = 'Producto'

    def __str__(self):
        return f'{self.codigo} – {self.nombre}'

    @property
    def estado_stock(self):
        if self.stock == 0:
            return 'sin_stock'
        if self.stock <= self.stock_minimo:
            return 'stock_bajo'
        return 'normal'
