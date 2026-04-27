from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre, password=None, **extra):
        if not email:
            raise ValueError('El email es requerido')
        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, **extra)
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
        ('Administrador', 'Administrador'),
        ('Vendedor',      'Vendedor'),
        ('Almacenista',   'Almacenista'),
        ('Contador',      'Contador'),
        ('Empleado',      'Empleado'),
    ]
    ESTADO_CHOICES = [('Activo', 'Activo'), ('Inactivo', 'Inactivo')]

    nombre       = models.CharField(max_length=150)
    email        = models.EmailField(unique=True)
    rol          = models.CharField(max_length=20, choices=ROL_CHOICES, default='Empleado')
    estado       = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Activo')
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    creado_en    = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    objects = UsuarioManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        db_table   = 'usuarios'
        verbose_name = 'Usuario'
        ordering   = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.rol})'
