from django.db import models
from productos.models import Producto
from users.models import Usuario


class Movimiento(models.Model):
    TIPO_CHOICES = [
        ('Entrada', 'Entrada'),
        ('Salida',  'Salida'),
        ('Ajuste',  'Ajuste'),
    ]

    producto    = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    tipo        = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad    = models.PositiveIntegerField()
    referencia  = models.CharField(max_length=100, blank=True)
    observacion = models.TextField(blank=True)
    creado_por  = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True,
                                    related_name='movimientos_creados')
    fecha       = models.DateField(auto_now_add=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table   = 'movimientos'
        ordering   = ['-fecha', '-id']
        verbose_name = 'Movimiento'

    def __str__(self):
        return f'{self.tipo} | {self.producto.nombre} | {self.cantidad}'
