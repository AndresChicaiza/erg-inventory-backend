import secrets
from django.db import models
from productos.models import Producto
from clientes.models import Cliente
from users.models import Usuario


# ─────────────────────────────────────────────────────────────────────────────
# Catálogo público — qué productos se muestran en el portal B2B
# ─────────────────────────────────────────────────────────────────────────────
class CatalogoPublico(models.Model):
    """
    Extiende un Producto del ERP para hacerlo visible en el portal de ventas B2B.
    Permite tener un precio, descripción e imagen diferentes al registro interno.
    """
    producto = models.OneToOneField(
        Producto,
        on_delete=models.CASCADE,
        related_name='catalogo_publico'
    )
    visible = models.BooleanField(
        default=False,
        help_text='Si está activo, el producto aparece en el portal B2B.'
    )
    descripcion_publica = models.TextField(
        blank=True,
        help_text='Descripción comercial para mostrar al cliente. Si está vacía, se usa la del producto.'
    )
    precio_publico = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Precio de lista en el portal. Si es 0, se usa el precio_venta del producto.'
    )
    imagen_publica = models.ImageField(
        upload_to='marketplace/',
        blank=True,
        null=True,
        help_text='Imagen para el portal. Si está vacía, se usa la imagen del producto.'
    )
    categoria_display = models.CharField(
        max_length=100,
        blank=True,
        help_text='Categoría a mostrar en el portal. Si está vacía, se usa la del producto.'
    )
    stock_maximo_pedido = models.DecimalField(
        max_digits=14,
        decimal_places=3,
        default=0,
        help_text='Cantidad máxima por pedido. 0 = sin límite.'
    )
    orden = models.IntegerField(
        default=0,
        help_text='Orden de aparición en el catálogo (menor = primero).'
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'marketplace_catalogo'
        ordering = ['orden', 'producto__nombre']
        verbose_name = 'Ítem de Catálogo'

    def __str__(self):
        return f'[{"✓" if self.visible else "✗"}] {self.producto.nombre}'

    @property
    def precio_efectivo(self):
        """Precio que se mostrará en el portal."""
        if self.precio_publico and self.precio_publico > 0:
            return self.precio_publico
        return self.producto.precio_venta

    @property
    def descripcion_efectiva(self):
        return self.descripcion_publica or self.producto.descripcion

    @property
    def categoria_efectiva(self):
        return self.categoria_display or self.producto.categoria

    @property
    def imagen_efectiva(self):
        """URL de la imagen: primero marketplace, luego producto."""
        if self.imagen_publica:
            return self.imagen_publica
        return self.producto.imagen

    @property
    def stock_disponible(self):
        return self.producto.stock


# ─────────────────────────────────────────────────────────────────────────────
# Pedido Online — pedidos que llegan desde el portal B2B
# ─────────────────────────────────────────────────────────────────────────────
class PedidoOnline(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente',  'Pendiente — por revisar'),
        ('En_Revision','En Revisión'),
        ('Aprobado',   'Aprobado → Factura creada'),
        ('Rechazado',  'Rechazado'),
    ]

    # ── Token de seguimiento (para el cliente sin login) ─────────────────────
    token = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        help_text='Token único para que el cliente consulte el estado del pedido sin login.'
    )

    # ── Datos del cliente (capturados en el portal) ──────────────────────────
    cliente_nit       = models.CharField(max_length=30, blank=True, help_text='NIT/CC del cliente')
    cliente_nombre    = models.CharField(max_length=250)
    cliente_email     = models.EmailField()
    cliente_telefono  = models.CharField(max_length=25, blank=True)
    cliente_ciudad    = models.CharField(max_length=100, blank=True)
    cliente_direccion = models.TextField(blank=True)
    notas             = models.TextField(blank=True, help_text='Observaciones del cliente')

    # ── Totales (calculados al crear) ────────────────────────────────────────
    subtotal = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    total    = models.DecimalField(max_digits=16, decimal_places=2, default=0)

    # ── Estado y trazabilidad ────────────────────────────────────────────────
    estado = models.CharField(
        max_length=15,
        choices=ESTADO_CHOICES,
        default='Pendiente'
    )
    motivo_rechazo = models.TextField(blank=True)

    # ── Vínculos al ERP (se llenan al aprobar) ───────────────────────────────
    cliente_erp = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pedidos_online',
        help_text='Cliente del ERP vinculado por NIT (si existe)'
    )
    factura = models.ForeignKey(
        'facturacion.Factura',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pedido_online_origen',
        help_text='Factura generada al aprobar el pedido'
    )
    revisado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pedidos_revisados'
    )
    revisado_en = models.DateTimeField(null=True, blank=True)

    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'marketplace_pedidos'
        ordering     = ['-creado_en']
        verbose_name = 'Pedido Online'

    def __str__(self):
        return f'PED-{self.pk:04d} | {self.cliente_nombre} | {self.estado}'

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def recalcular_totales(self):
        sub = sum(d.subtotal_linea for d in self.detalles.all())
        self.subtotal = sub
        self.total = sub
        self.save(update_fields=['subtotal', 'total'])


# ─────────────────────────────────────────────────────────────────────────────
# Detalle del Pedido Online
# ─────────────────────────────────────────────────────────────────────────────
class DetallePedidoOnline(models.Model):
    pedido         = models.ForeignKey(
        PedidoOnline,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    catalogo_item  = models.ForeignKey(
        CatalogoPublico,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    # Snapshot al momento del pedido (para historial)
    producto       = models.ForeignKey(
        Producto,
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    nombre_producto = models.CharField(max_length=200)
    cantidad        = models.DecimalField(max_digits=12, decimal_places=3)
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2)
    subtotal_linea  = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        db_table = 'marketplace_detalles'

    def save(self, *args, **kwargs):
        self.subtotal_linea = round(self.cantidad * self.precio_unitario, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.nombre_producto} × {self.cantidad}'
