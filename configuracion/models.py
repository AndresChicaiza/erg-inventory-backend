from django.db import models


class ConfiguracionEmpresa(models.Model):
    """
    Registro único con los datos de Suministros Dacar S.A.S.
    Solo el Administrador puede modificarlo.
    """
    # ── Identificación ───────────────────────────────────────────
    nit                  = models.CharField(max_length=20, default='901334172')
    digito_verificacion  = models.CharField(max_length=1, default='0')
    razon_social         = models.CharField(max_length=250, default='SUMINISTROS DACAR S.A.S.')
    nombre_comercial     = models.CharField(max_length=250, default='VOLCANO ASADORES')

    # ── Contacto ─────────────────────────────────────────────────
    direccion            = models.TextField(default='CR 17 G # 25 – 78')
    ciudad               = models.CharField(max_length=100, default='Cali')
    departamento         = models.CharField(max_length=100, default='Valle del Cauca')
    telefono             = models.CharField(max_length=25, default='316 691 4910')
    telefono2            = models.CharField(max_length=25, default='312 780 1986')
    email                = models.EmailField(default='suministrosdacar@gmail.com')
    email_notificaciones = models.EmailField(
                               default='chicaizapipe@gmail.com',
                               help_text='Email desde donde se envían las facturas'
                           )

    # ── Tributario ───────────────────────────────────────────────
    ciiu                 = models.CharField(max_length=10, default='4659')
    regimen              = models.CharField(
                               max_length=50,
                               default='Responsable de IVA'
                           )
    responsabilidades    = models.CharField(
                               max_length=200,
                               default='07-Retención en la fuente, 09-Retención IVA, 48-IVA, 52-Facturador electrónico'
                           )
    agente_retenedor     = models.BooleanField(default=True)
    gran_contribuyente   = models.BooleanField(default=False)

    # ── Facturación ──────────────────────────────────────────────
    prefijo_factura      = models.CharField(max_length=10, default='FACT')
    resolucion_numero    = models.CharField(max_length=50, blank=True,
                               help_text='Número de resolución DIAN — se llena cuando esté disponible')
    resolucion_fecha     = models.DateField(null=True, blank=True)
    resolucion_vigencia  = models.DateField(null=True, blank=True)
    rango_desde          = models.PositiveIntegerField(default=1)
    rango_hasta          = models.PositiveIntegerField(default=1000)
    consecutivo_actual   = models.PositiveIntegerField(default=1)

    # ── IVA por defecto ──────────────────────────────────────────
    iva_default          = models.DecimalField(
                               max_digits=5, decimal_places=2, default=19.00,
                               help_text='Tarifa IVA por defecto (%)'
                           )

    # ── Logo ─────────────────────────────────────────────────────
    logo                 = models.ImageField(
                               upload_to='configuracion/', null=True, blank=True,
                               help_text='Logo de la empresa para facturas'
                           )

    # ── Meta ─────────────────────────────────────────────────────
    actualizado_en       = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'configuracion_empresa'
        verbose_name = 'Configuración de Empresa'

    def __str__(self):
        return f'{self.razon_social} — NIT {self.nit}-{self.digito_verificacion}'

    @property
    def nit_completo(self):
        return f'{self.nit}-{self.digito_verificacion}'

    def siguiente_consecutivo(self):
        """Retorna el próximo número de factura e incrementa el contador."""
        num = self.consecutivo_actual
        self.consecutivo_actual += 1
        self.save(update_fields=['consecutivo_actual'])
        return num

    def numero_factura_formateado(self, numero):
        return f'{self.prefijo_factura}-{str(numero).zfill(4)}'

    def save(self, *args, **kwargs):
        # Garantiza que solo exista un registro
        self.pk = 1
        super().save(*args, **kwargs)


class TarifaReteICA(models.Model):
    """
    Tarifas de ReteICA por ciudad y actividad CIIU.
    Pre-cargadas para las principales ciudades de Colombia.
    """
    ciudad          = models.CharField(max_length=100)
    departamento    = models.CharField(max_length=100, blank=True)
    ciiu_desde      = models.CharField(max_length=10, blank=True,
                          help_text='Código CIIU inicio del rango')
    ciiu_hasta      = models.CharField(max_length=10, blank=True,
                          help_text='Código CIIU fin del rango')
    descripcion     = models.CharField(max_length=200, blank=True)
    tarifa_por_mil  = models.DecimalField(max_digits=6, decimal_places=3,
                          help_text='Tarifa en por mil (‰)')
    activo          = models.BooleanField(default=True)

    class Meta:
        db_table     = 'tarifas_reteica'
        ordering     = ['ciudad', 'ciiu_desde']
        verbose_name = 'Tarifa ReteICA'

    def __str__(self):
        return f'{self.ciudad} — {self.tarifa_por_mil}‰'


class TarifaRetefuente(models.Model):
    """
    Tarifas de Retefuente por concepto.
    Actualizables cada año según la UVT.
    """
    CONCEPTO_CHOICES = [
        ('COMPRAS',       'Compras generales'),
        ('SERVICIOS',     'Servicios generales'),
        ('HONORARIOS',    'Honorarios'),
        ('ARRENDAMIENTO', 'Arrendamiento'),
        ('TRANSPORTE',    'Transporte de carga'),
        ('OTROS',         'Otros'),
    ]

    concepto          = models.CharField(max_length=20, choices=CONCEPTO_CHOICES, unique=True)
    descripcion       = models.CharField(max_length=200)
    tarifa_porcentaje = models.DecimalField(max_digits=5, decimal_places=2,
                            help_text='Tarifa en porcentaje (%)')
    cuantia_minima    = models.DecimalField(max_digits=14, decimal_places=2,
                            help_text='Valor mínimo de la factura para aplicar retención')
    uvt_referencia    = models.IntegerField(default=2025,
                            help_text='Año fiscal de referencia')
    activo            = models.BooleanField(default=True)

    class Meta:
        db_table     = 'tarifas_retefuente'
        verbose_name = 'Tarifa Retefuente'

    def __str__(self):
        return f'{self.get_concepto_display()} — {self.tarifa_porcentaje}%'