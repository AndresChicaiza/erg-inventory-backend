from django.db import models
from django.utils import timezone
from productos.models import Producto
from facturacion.models import Factura
from users.models import Usuario

class Receta(models.Model):
    producto_terminado = models.OneToOneField(
        Producto, on_delete=models.CASCADE, related_name='receta',
        limit_choices_to={'tipo_inventario': 'TERMINADO'}
    )
    descripcion = models.TextField(blank=True)
    costo_estimado = models.DecimalField(max_digits=14, decimal_places=2, default=0, editable=False)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'produccion_recetas'
        verbose_name = 'Receta'

    def __str__(self):
        return f'Receta de {self.producto_terminado.nombre}'

    def calcular_costo_estimado(self):
        costo = sum([i.producto_materia.precio_costo * i.cantidad_esperada for i in self.ingredientes.all()])
        self.costo_estimado = costo
        self.save(update_fields=['costo_estimado'])


class IngredienteReceta(models.Model):
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE, related_name='ingredientes')
    producto_materia = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name='usado_en_recetas'
    )
    cantidad_esperada = models.DecimalField(max_digits=12, decimal_places=3)

    class Meta:
        db_table = 'produccion_ingredientes'
        unique_together = ('receta', 'producto_materia')

    def __str__(self):
        return f'{self.cantidad_esperada} {self.producto_materia.unidad_medida} de {self.producto_materia.nombre}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.receta.calcular_costo_estimado()

    def delete(self, *args, **kwargs):
        receta = self.receta
        super().delete(*args, **kwargs)
        receta.calcular_costo_estimado()


class OrdenProduccion(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('En_Proceso', 'En Proceso'),
        ('Completada', 'Completada'),
        ('Cancelada', 'Cancelada'),
    ]
    
    numero = models.CharField(max_length=20, unique=True, editable=False)
    receta = models.ForeignKey(Receta, on_delete=models.PROTECT, related_name='ordenes')
    cantidad_a_fabricar = models.IntegerField(default=1)
    
    bodega = models.ForeignKey(
        'bodegas.Bodega', on_delete=models.PROTECT, related_name='ordenes_produccion',
        null=True, blank=True, help_text="De dónde sale la materia prima y adónde entra el terminado"
    )
    
    # Opcional: si viene de vender algo sin stock
    factura_vinculada = models.ForeignKey(
        Factura, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='ordenes_produccion'
    )
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')
    notas = models.TextField(blank=True)
    
    fecha_inicio = models.DateTimeField(null=True, blank=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    
    creado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='ordenes_creadas')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'produccion_ordenes'
        ordering = ['-creado_en']
        verbose_name = 'Orden de Producción'

    def __str__(self):
        return f'ORD-{self.numero} | {self.receta.producto_terminado.nombre} (x{self.cantidad_a_fabricar})'

    def save(self, *args, **kwargs):
        if not self.numero:
            last = OrdenProduccion.objects.order_by('-id').first()
            idx = (last.id + 1) if last else 1
            self.numero = f'PRD-{str(idx).zfill(5)}'
            
        if self.estado == 'En_Proceso' and not self.fecha_inicio:
            self.fecha_inicio = timezone.now()
        if self.estado == 'Completada' and not self.fecha_fin:
            self.fecha_fin = timezone.now()
            
        super().save(*args, **kwargs)


class ConsumoProduccion(models.Model):
    orden = models.ForeignKey(OrdenProduccion, on_delete=models.CASCADE, related_name='consumos')
    producto_materia = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='consumos_produccion')
    cantidad_esperada = models.DecimalField(max_digits=12, decimal_places=3, help_text="Calculada: receta * cantidad_a_fabricar")
    cantidad_real = models.DecimalField(max_digits=12, decimal_places=3, default=0, help_text="Lo que el operario dice que gastó realmente")

    class Meta:
        db_table = 'produccion_consumos'
        unique_together = ('orden', 'producto_materia')

    def __str__(self):
        return f'{self.producto_materia.nombre} | Real: {self.cantidad_real}'
