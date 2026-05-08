from django.db import models
from django.utils import timezone
from clientes.models import Cliente
from productos.models import Producto
from users.models import Usuario


class Factura(models.Model):

    ESTADO_CHOICES = [
        ('Borrador',  'Borrador'),
        ('Emitida',   'Emitida'),
        ('Pagada',    'Pagada'),
        ('Vencida',   'Vencida'),
        ('Anulada',   'Anulada'),
    ]

    CONDICION_CHOICES = [
        ('Contado',     'Contado'),
        ('15_dias',     'Crédito 15 días'),
        ('30_dias',     'Crédito 30 días'),
        ('60_dias',     'Crédito 60 días'),
        ('90_dias',     'Crédito 90 días'),
    ]

    MEDIO_PAGO_CHOICES = [
        ('Efectivo',      'Efectivo'),
        ('Debito',        'Tarjeta Débito'),
        ('Credito',       'Tarjeta Crédito'),
        ('Transferencia', 'Transferencia Bancaria'),
        ('ADDI',          'ADDI'),
        ('Distecredito',  'Distecredito'),
        ('Cheque',        'Cheque'),
        ('Otro',          'Otro'),
    ]

    CONCEPTO_RETEFUENTE_CHOICES = [
        ('COMPRAS',       'Compras generales (2.5%)'),
        ('SERVICIOS',     'Servicios (4%)'),
        ('HONORARIOS',    'Honorarios (11%)'),
        ('ARRENDAMIENTO', 'Arrendamiento (3.5%)'),
        ('TRANSPORTE',    'Transporte (1%)'),
        ('OTROS',         'Otros (2.5%)'),
    ]

    # ── Numeración ───────────────────────────────────────────────
    numero           = models.PositiveIntegerField(unique=True, editable=False)
    prefijo          = models.CharField(max_length=10, default='FACT')
    numero_completo  = models.CharField(max_length=20, unique=True, editable=False)

    # ── Cliente ──────────────────────────────────────────────────
    cliente          = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='facturas')

    # ── Fechas ───────────────────────────────────────────────────
    fecha_emision    = models.DateField(default=timezone.now)
    fecha_vencimiento= models.DateField(null=True, blank=True)

    # ── Condiciones ──────────────────────────────────────────────
    condicion_pago   = models.CharField(max_length=15, choices=CONDICION_CHOICES, default='Contado')
    medio_pago       = models.CharField(max_length=15, choices=MEDIO_PAGO_CHOICES, default='Efectivo')
    concepto_retefuente = models.CharField(
        max_length=15, choices=CONCEPTO_RETEFUENTE_CHOICES,
        default='COMPRAS', blank=True
    )

    # ── Totales calculados ───────────────────────────────────────
    subtotal             = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    descuento_total      = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    base_iva_0           = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    base_iva_5           = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    base_iva_19          = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    base_excluida        = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    valor_iva_5          = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    valor_iva_19         = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    valor_iva_total      = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    retefuente_pct       = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    valor_retefuente     = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    reteiva_pct          = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    valor_reteiva        = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    reteica_pct          = models.DecimalField(max_digits=8, decimal_places=3, default=0)
    valor_reteica        = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    total_retenciones    = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    total_a_pagar        = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    # ── Estado ───────────────────────────────────────────────────
    estado           = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Borrador')
    notas            = models.TextField(blank=True)

    # ── DIAN (futuro) ────────────────────────────────────────────
    cufe             = models.CharField(max_length=200, blank=True,
                           help_text='Código único DIAN — se llena al conectar con la DIAN')
    qr_url           = models.TextField(blank=True)

    # ── Trazabilidad ─────────────────────────────────────────────
    creado_por       = models.ForeignKey(Usuario, on_delete=models.SET_NULL,
                           null=True, related_name='facturas_creadas')
    emitida_por      = models.ForeignKey(Usuario, on_delete=models.SET_NULL,
                           null=True, blank=True, related_name='facturas_emitidas')
    fecha_emision_ts = models.DateTimeField(null=True, blank=True)
    creado_en        = models.DateTimeField(auto_now_add=True)
    actualizado_en   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'facturas'
        ordering     = ['-numero']
        verbose_name = 'Factura'

    def __str__(self):
        return f'{self.numero_completo} | {self.cliente.razon_social} | {self.estado}'

    def save(self, *args, **kwargs):
        # Asignar consecutivo automático al crear
        if not self.numero:
            from configuracion.models import ConfiguracionEmpresa
            config = ConfiguracionEmpresa.objects.first()
            if config:
                self.numero         = config.siguiente_consecutivo()
                self.prefijo        = config.prefijo_factura
                self.numero_completo = config.numero_factura_formateado(self.numero)
            else:
                self.numero          = 1
                self.prefijo         = 'FACT'
                self.numero_completo = 'FACT-0001'

        # Calcular fecha de vencimiento según condición de pago
        if not self.fecha_vencimiento:
            dias = {
                'Contado': 0, '15_dias': 15,
                '30_dias': 30, '60_dias': 60, '90_dias': 90,
            }.get(self.condicion_pago, 0)
            self.fecha_vencimiento = self.fecha_emision + timezone.timedelta(days=dias)

        super().save(*args, **kwargs)

    def recalcular_totales(self):
        """Recalcula todos los totales a partir de los ítems."""
        from .calculadora import calcular_factura
        calcular_factura(self)


class DetalleFactura(models.Model):
    IVA_CHOICES = [
        ('0',        'Exento (0%)'),
        ('5',        'IVA 5%'),
        ('19',       'IVA 19%'),
        ('EXCLUIDO', 'Excluido de IVA'),
    ]

    factura          = models.ForeignKey(Factura, on_delete=models.CASCADE, related_name='detalles')
    producto         = models.ForeignKey(Producto, on_delete=models.SET_NULL,
                           null=True, blank=True, related_name='detalles_factura')

    # El usuario puede editar la descripción aunque venga del producto
    descripcion      = models.CharField(max_length=300)
    cantidad         = models.DecimalField(max_digits=12, decimal_places=3)
    precio_unitario  = models.DecimalField(max_digits=14, decimal_places=2)
    descuento_pct    = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    es_obsequio      = models.BooleanField(default=False,
                           help_text='Descuento 100% — ítem aparece como obsequio en la factura')

    iva_tipo         = models.CharField(max_length=10, choices=IVA_CHOICES, default='19')

    # Calculados
    valor_descuento  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    subtotal_linea   = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_iva_linea  = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_linea      = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    orden            = models.PositiveIntegerField(default=0)

    class Meta:
        db_table  = 'factura_detalles'
        ordering  = ['orden', 'id']

    def save(self, *args, **kwargs):
        # Si es obsequio → descuento 100%
        if self.es_obsequio:
            self.descuento_pct = 100

        base               = self.cantidad * self.precio_unitario
        self.valor_descuento = round(base * self.descuento_pct / 100, 2)
        self.subtotal_linea  = round(base - self.valor_descuento, 2)

        if self.iva_tipo in ('0', 'EXCLUIDO') or self.es_obsequio:
            self.valor_iva_linea = 0
        elif self.iva_tipo == '5':
            self.valor_iva_linea = round(self.subtotal_linea * 5 / 100, 2)
        elif self.iva_tipo == '19':
            self.valor_iva_linea = round(self.subtotal_linea * 19 / 100, 2)
        else:
            self.valor_iva_linea = 0

        self.total_linea = self.subtotal_linea + self.valor_iva_linea
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.factura.numero_completo} | {self.descripcion}'


class NotaCredito(models.Model):
    MOTIVO_CHOICES = [
        ('DEVOLUCION',  'Devolución de mercancía'),
        ('DESCUENTO',   'Descuento comercial'),
        ('ANULACION',   'Anulación de factura'),
        ('PRECIO',      'Ajuste de precio'),
        ('OTRO',        'Otro'),
    ]

    factura_original = models.ForeignKey(Factura, on_delete=models.PROTECT,
                           related_name='notas_credito')
    numero           = models.PositiveIntegerField(unique=True, editable=False)
    numero_completo  = models.CharField(max_length=20, unique=True, editable=False)
    motivo           = models.CharField(max_length=15, choices=MOTIVO_CHOICES)
    descripcion      = models.TextField()

    subtotal         = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    valor_iva        = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    total            = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    creado_por       = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    creado_en        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table     = 'notas_credito'
        ordering     = ['-creado_en']
        verbose_name = 'Nota Crédito'

    def __str__(self):
        return f'NC-{self.numero_completo} → {self.factura_original.numero_completo}'

    def save(self, *args, **kwargs):
        if not self.numero:
            last = NotaCredito.objects.order_by('-numero').first()
            self.numero         = (last.numero + 1) if last else 1
            self.numero_completo = f'NC-{str(self.numero).zfill(4)}'
        super().save(*args, **kwargs)