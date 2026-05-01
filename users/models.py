from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Sede(models.Model):
    TIPO_CHOICES = [
        ('FABRICA',   'Fábrica'),
        ('TIENDA',    'Tienda'),
        ('MERCADEO',  'Mercadeo'),
        ('LOGISTICA', 'Logística'),
        ('OFICINA',   'Oficina'),
    ]
    ESTADO_CHOICES = [('Activa', 'Activa'), ('Inactiva', 'Inactiva')]

    nombre    = models.CharField(max_length=100, unique=True)
    tipo      = models.CharField(max_length=10, choices=TIPO_CHOICES)
    ciudad    = models.CharField(max_length=100, default='Cali')
    direccion = models.TextField(blank=True)
    telefono  = models.CharField(max_length=25, blank=True)
    estado    = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Activa')
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table     = 'sedes'
        ordering     = ['nombre']
        verbose_name = 'Sede'

    def __str__(self):
        return self.nombre


class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre, password=None, **extra):
        if not email:
            raise ValueError('El email es requerido')
        email = self.normalize_email(email)
        user  = self.model(email=email, nombre=nombre, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, password=None, **extra):
        extra.setdefault('rol', 'Administrador')
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, nombre, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    ROL_CHOICES = [
        ('Administrador',  'Administrador'),
        ('Contador',       'Contador'),
        ('Vendedor',       'Vendedor'),
        ('Logistica',      'Logística'),
        ('JefeFabrica',    'Jefe de Fábrica'),
        ('Bodeguero',      'Bodeguero'),
        ('RRHH',           'RRHH'),
    ]
    ESTADO_CHOICES = [('Activo', 'Activo'), ('Inactivo', 'Inactivo')]

    nombre         = models.CharField(max_length=150)
    email          = models.EmailField(unique=True)
    rol            = models.CharField(max_length=20, choices=ROL_CHOICES, default='Vendedor')
    sede           = models.ForeignKey(
                         Sede, on_delete=models.SET_NULL,
                         null=True, blank=True, related_name='usuarios'
                     )
    telefono       = models.CharField(max_length=25, blank=True)
    estado         = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Activo')
    is_active      = models.BooleanField(default=True)
    is_staff       = models.BooleanField(default=False)
    creado_en      = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    objects = UsuarioManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        db_table     = 'usuarios'
        verbose_name = 'Usuario'
        ordering     = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.get_rol_display()})'

    # ── helpers de rol ──────────────────────────────────────────
    @property
    def es_admin(self):
        return self.rol == 'Administrador'

    @property
    def es_contador(self):
        return self.rol == 'Contador'

    @property
    def es_vendedor(self):
        return self.rol == 'Vendedor'

    @property
    def es_logistica(self):
        return self.rol == 'Logistica'

    @property
    def es_jefe_fabrica(self):
        return self.rol == 'JefeFabrica'

    @property
    def es_bodeguero(self):
        return self.rol == 'Bodeguero'

    @property
    def es_rrhh(self):
        return self.rol == 'RRHH'

    @property
    def puede_ver_costos(self):
        return self.rol in ('Administrador', 'Contador')

    @property
    def puede_crear_productos(self):
        return self.rol in ('Administrador', 'Contador')

    @property
    def puede_aprobar_oc(self):
        return self.rol in ('Administrador', 'Contador')

    @property
    def puede_facturar(self):
        return self.rol in ('Administrador', 'Contador')