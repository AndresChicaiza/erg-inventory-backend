from django.db import models


class Producto(models.Model):

    ESTADO_CHOICES = [('Activo', 'Activo'), ('Inactivo', 'Inactivo')]

    UNIDAD_CHOICES = [
        ('UND',  'Unidades'),
        ('KG',   'Kilogramos'),
        ('GR',   'Gramos'),
        ('LT',   'Litros'),
        ('ML',   'Mililitros'),
        ('MT',   'Metros'),
        ('MT2',  'Metros cuadrados'),
        ('MT3',  'Metros cúbicos'),
        ('ROLLO','Rollos'),
        ('CJA',  'Cajas'),
        ('BLS',  'Bolsas'),
    ]

    IVA_TIPO_CHOICES = [
        ('19',       'IVA 19%'),
        ('5',        'IVA 5%'),
        ('0',        'Exento (0%)'),
        ('EXCLUIDO', 'Excluido de IVA'),
    ]

    TIPO_INVENTARIO_CHOICES = [
        ('TERMINADO',    'Producto Terminado'),
        ('MATERIA_PRIMA','Materia Prima'),
        ('TIENDA',       'Producto de Tienda'),
    ]

    # ── Identificación ───────────────────────────────────────────
    codigo         = models.CharField(max_length=30, unique=True)
    codigo_barras  = models.CharField(max_length=100, blank=True, null=True, help_text="Código EAN o UPC")
    nombre         = models.CharField(max_length=200)
    descripcion    = models.TextField(blank=True)
    categoria      = models.CharField(max_length=100)
    imagen         = models.ImageField(upload_to='productos/', blank=True, null=True)

    # ── Tipo de inventario ───────────────────────────────────────
    tipo_inventario = models.CharField(
                          max_length=15,
                          choices=TIPO_INVENTARIO_CHOICES,
                          default='TERMINADO'
                      )
    
    # ── Control de Lotes ─────────────────────────────────────────
    controla_vencimiento = models.BooleanField(
        default=False,
        help_text="Activar para productos perecederos (carnes, condimentos) que requieren Lote y Fecha de Vencimiento."
    )

    # ── Unidad de medida ─────────────────────────────────────────
    unidad_medida  = models.CharField(
                         max_length=10,
                         choices=UNIDAD_CHOICES,
                         default='UND'
                     )

    # ── Precios ──────────────────────────────────────────────────
    precio_venta   = models.DecimalField(max_digits=14, decimal_places=2)
    precio_costo   = models.DecimalField(max_digits=14, decimal_places=2)

    # ── IVA ──────────────────────────────────────────────────────
    iva_tipo       = models.CharField(
                         max_length=10,
                         choices=IVA_TIPO_CHOICES,
                         default='19',
                         help_text='Tipo de IVA que aplica a este producto'
                     )
    iva_incluido   = models.BooleanField(
                         default=False,
                         help_text=(
                             'Si está activo, el precio de venta ya incluye el IVA. '
                             'Al facturar se discrimina automáticamente la base y el IVA.'
                         )
                     )

    # ── Stock ────────────────────────────────────────────────────
    stock          = models.IntegerField(default=0)
    stock_minimo   = models.IntegerField(default=5)

    # ── Estado ───────────────────────────────────────────────────
    estado         = models.CharField(
                         max_length=10,
                         choices=ESTADO_CHOICES,
                         default='Activo'
                     )
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'productos'
        ordering     = ['nombre']
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

    @property
    def precio_sin_iva(self):
        """
        Si el precio tiene IVA incluido, retorna la base sin IVA.
        Útil para discriminar el IVA en la factura.
        """
        if not self.iva_incluido or self.iva_tipo not in ('19', '5'):
            return self.precio_venta

        from decimal import Decimal
        divisor = {
            '19': Decimal('1.19'),
            '5':  Decimal('1.05'),
        }.get(self.iva_tipo, Decimal('1'))

        return round(self.precio_venta / divisor, 2)

    @property
    def valor_iva_unitario(self):
        """Valor del IVA por unidad cuando el precio incluye IVA."""
        if not self.iva_incluido:
            return 0
        return round(float(self.precio_venta) - float(self.precio_sin_iva), 2)


class Lote(models.Model):
    ESTADO_CHOICES = [
        ('Vigente', 'Vigente'),
        ('Por Vencer', 'Por Vencer (<= 30 días)'),
        ('Vencido', 'Vencido'),
        ('Agotado', 'Agotado')
    ]

    producto          = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='lotes')
    numero_lote       = models.CharField(max_length=100)
    fecha_vencimiento = models.DateField()
    stock_disponible  = models.IntegerField(default=0)
    estado            = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Vigente')
    creado_en         = models.DateTimeField(auto_now_add=True)
    actualizado_en    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lotes'
        ordering = ['fecha_vencimiento']
        unique_together = ('producto', 'numero_lote')

    def __str__(self):
        return f'{self.numero_lote} (Vence: {self.fecha_vencimiento})'