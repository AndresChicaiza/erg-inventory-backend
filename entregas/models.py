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

    TIPO_ENTREGA_CHOICES = [
        ('Venta', 'Despacho de Venta'),
        ('Traslado', 'Traslado entre Bodegas'),
    ]

    METODO_ENVIO_CHOICES = [
        ('Propio', 'Vehículo Propio'),
        ('Transportadora', 'Transportadora Externa'),
    ]

    tipo_entrega    = models.CharField(max_length=15, choices=TIPO_ENTREGA_CHOICES, default='Venta')
    
    # ── Relaciones ──
    factura         = models.ForeignKey('facturacion.Factura', on_delete=models.SET_NULL, null=True, blank=True, related_name='entregas')
    cliente         = models.ForeignKey(Cliente, on_delete=models.PROTECT, null=True, blank=True, related_name='entregas')
    bodega_origen   = models.ForeignKey('bodegas.Bodega', on_delete=models.PROTECT, null=True, blank=True, related_name='traslados_salientes')
    bodega_destino  = models.ForeignKey('bodegas.Bodega', on_delete=models.PROTECT, null=True, blank=True, related_name='traslados_entrantes')
    
    # ── Logística ──
    direccion       = models.TextField(blank=True)
    metodo_envio    = models.CharField(max_length=20, choices=METODO_ENVIO_CHOICES, default='Propio')
    transportista   = models.CharField(max_length=150, blank=True, help_text="Nombre del conductor o de la empresa externa (ej. Envia, Inter Rapidisimo)")
    numero_guia     = models.CharField(max_length=100, blank=True)
    
    estado          = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='Pendiente')
    fecha_estimada  = models.DateField(null=True, blank=True)
    fecha_entregada = models.DateField(null=True, blank=True)
    notas           = models.TextField(blank=True)
    
    creado_por      = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='entregas_creadas')
    creado_en       = models.DateTimeField(auto_now_add=True)
    actualizado_en  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table   = 'entregas'
        ordering   = ['-creado_en']
        verbose_name = 'Entrega'

    def __str__(self):
        cliente_nombre = self.cliente.razon_social if self.cliente else (self.bodega_destino.nombre if self.bodega_destino else 'Desconocido')
        return f'ENT-{self.id:04d} | {cliente_nombre} | {self.estado}'


class DetalleEntrega(models.Model):
    entrega  = models.ForeignKey(Entrega, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    
    class Meta:
        db_table = 'entrega_detalles'

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'
