from django.db import models
from clientes.models import Cliente
from users.models import Usuario


class Entrega(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente',   'Pendiente'),
        ('En Tránsito', 'En Tránsito'),
        ('Entregada',   'Entregada'),
        ('Fallida',     'Fallida'),
    ]

    cliente         = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='entregas')
    direccion       = models.TextField()
    transportista   = models.CharField(max_length=150)
    estado          = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='Pendiente')
    fecha_estimada  = models.DateField(null=True, blank=True)
    fecha_entregada = models.DateField(null=True, blank=True)
    notas           = models.TextField(blank=True)
    creado_por      = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True,
                                        related_name='entregas_creadas')
    creado_en       = models.DateTimeField(auto_now_add=True)
    actualizado_en  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table   = 'entregas'
        ordering   = ['-creado_en']
        verbose_name = 'Entrega'

    def __str__(self):
        return f'ENT-{self.id:04d} | {self.cliente.nombre} | {self.estado}'
