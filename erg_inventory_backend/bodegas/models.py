from django.db import models
from users.models import Usuario


class Bodega(models.Model):
    ESTADO_CHOICES = [('Activa', 'Activa'), ('Inactiva', 'Inactiva')]

    nombre      = models.CharField(max_length=200)
    codigo      = models.CharField(max_length=20, unique=True)
    direccion   = models.TextField(blank=True)
    ciudad      = models.CharField(max_length=100, blank=True)
    responsable = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='bodegas')
    estado      = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Activa')
    descripcion = models.TextField(blank=True)
    creado_en   = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bodegas'
        ordering = ['nombre']
        verbose_name = 'Bodega'

    def __str__(self):
        return f'{self.codigo} – {self.nombre}'


class StockBodega(models.Model):
    """Stock de cada producto por bodega."""
    bodega   = models.ForeignKey(Bodega, on_delete=models.CASCADE, related_name='stocks')
    producto = models.ForeignKey('productos.Producto', on_delete=models.CASCADE, related_name='stocks_bodega')
    cantidad = models.IntegerField(default=0)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stock_bodega'
        unique_together = ('bodega', 'producto')
        verbose_name = 'Stock por Bodega'

    def __str__(self):
        return f'{self.bodega.nombre} | {self.producto.nombre} | {self.cantidad}'
