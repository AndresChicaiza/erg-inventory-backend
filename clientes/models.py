from django.db import models


class Cliente(models.Model):

    # ── Tipo de documento ────────────────────────────────────────
    TIPO_DOC_CHOICES = [
        ('NIT',           'NIT'),
        ('CC',            'Cédula de Ciudadanía'),
        ('CE',            'Cédula de Extranjería'),
        ('PASAPORTE',     'Pasaporte'),
        ('NIT_EXTRAN',    'NIT Extranjero'),
        ('RUT',           'RUT'),
    ]

    # ── Régimen tributario ───────────────────────────────────────
    REGIMEN_CHOICES = [
        ('RESPONSABLE_IVA',   'Responsable de IVA'),
        ('NO_RESPONSABLE',    'No Responsable de IVA'),
        ('REGIMEN_SIMPLE',    'Régimen Simple de Tributación'),
        ('GRAN_CONTRIBUYENTE','Gran Contribuyente'),
        ('ESPECIAL',          'Entidad sin ánimo de lucro'),
        ('PERSONA_NATURAL',   'Persona Natural no comerciante'),
    ]

    ESTADO_CHOICES = [('Activo', 'Activo'), ('Inactivo', 'Inactivo')]

    # ── Identificación (llave lógica principal) ──────────────────
    tipo_documento      = models.CharField(max_length=12, choices=TIPO_DOC_CHOICES, default='NIT')
    numero_documento    = models.CharField(max_length=20, unique=True)
    digito_verificacion = models.CharField(max_length=1, blank=True,
                                           help_text='Solo para NIT')

    # ── Datos básicos ────────────────────────────────────────────
    razon_social        = models.CharField(max_length=250)
    nombre_comercial    = models.CharField(max_length=250, blank=True)

    # ── Contacto ─────────────────────────────────────────────────
    email               = models.EmailField(blank=True)
    telefono            = models.CharField(max_length=25, blank=True)
    telefono2           = models.CharField(max_length=25, blank=True)

    # ── Ubicación ────────────────────────────────────────────────
    direccion           = models.TextField(blank=True)
    ciudad              = models.CharField(max_length=100, blank=True)
    departamento        = models.CharField(max_length=100, blank=True)
    pais                = models.CharField(max_length=100, default='Colombia')

    # ── Tributario ───────────────────────────────────────────────
    regimen_tributario  = models.CharField(
                              max_length=20,
                              choices=REGIMEN_CHOICES,
                              default='RESPONSABLE_IVA'
                          )
    responsable_iva     = models.BooleanField(default=True)
    gran_contribuyente  = models.BooleanField(default=False)
    agente_retenedor    = models.BooleanField(default=False,
                              help_text='Si aplica retenciones al pagar')
    autoretenedor       = models.BooleanField(default=False)

    # ── Actividad económica ──────────────────────────────────────
    ciiu                = models.CharField(max_length=10, blank=True,
                              help_text='Código CIIU de actividad económica')

    # ── Estado ───────────────────────────────────────────────────
    estado              = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Activo')
    notas               = models.TextField(blank=True)

    # ── Trazabilidad ─────────────────────────────────────────────
    creado_por          = models.ForeignKey(
                              'users.Usuario', on_delete=models.SET_NULL,
                              null=True, blank=True, related_name='clientes_creados'
                          )
    creado_en           = models.DateTimeField(auto_now_add=True)
    actualizado_en      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table     = 'clientes'
        ordering     = ['razon_social']
        verbose_name = 'Cliente'

    def __str__(self):
        dv = f'-{self.digito_verificacion}' if self.digito_verificacion else ''
        return f'{self.razon_social} ({self.tipo_documento}: {self.numero_documento}{dv})'

    @property
    def documento_completo(self):
        """Retorna el documento formateado: NIT: 900.123.456-7"""
        dv = f'-{self.digito_verificacion}' if self.digito_verificacion else ''
        return f'{self.tipo_documento}: {self.numero_documento}{dv}'

    @property
    def aplica_retefuente(self):
        return self.agente_retenedor

    @property
    def aplica_reteiva(self):
        return self.gran_contribuyente or (
            self.responsable_iva and self.agente_retenedor
        )

    # ── Exógena (Formatos 1008/1009) ─────────────────────────────
    @property
    def exogena_primer_apellido(self):
        if self.tipo_documento != 'CC': return ''
        parts = self.razon_social.split()
        return parts[0] if len(parts) > 0 else ''

    @property
    def exogena_segundo_apellido(self):
        if self.tipo_documento != 'CC': return ''
        parts = self.razon_social.split()
        return parts[1] if len(parts) > 1 else ''

    @property
    def exogena_primer_nombre(self):
        if self.tipo_documento != 'CC': return ''
        parts = self.razon_social.split()
        return parts[2] if len(parts) > 2 else ''

    @property
    def exogena_segundo_nombre(self):
        if self.tipo_documento != 'CC': return ''
        parts = self.razon_social.split()
        return " ".join(parts[3:]) if len(parts) > 3 else ''

    @property
    def exogena_razon_social(self):
        if self.tipo_documento == 'CC': return ''
        return self.razon_social