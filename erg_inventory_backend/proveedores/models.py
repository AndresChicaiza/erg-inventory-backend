from django.db import models

class Proveedor(models.Model):
    CATEGORIA_CHOICES = [('Nacional', 'Nacional'), ('Internacional', 'Internacional')]
    TIPO_CHOICES      = [('Estándar', 'Estándar'), ('Preferido', 'Preferido')]
    ESTADO_CHOICES    = [('Activo', 'Activo'), ('Inactivo', 'Inactivo')]

    empresa   = models.CharField(max_length=200)
    contacto  = models.CharField(max_length=150, blank=True)
    email     = models.EmailField(blank=True)
    telefono  = models.CharField(max_length=25, blank=True)
    ciudad    = models.CharField(max_length=100, blank=True)
    categoria = models.CharField(max_length=15, choices=CATEGORIA_CHOICES, default='Nacional')
    tipo      = models.CharField(max_length=10, choices=TIPO_CHOICES, default='Estándar')
    estado    = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Activo')
    creado_en    = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'proveedores'
        ordering = ['empresa']
        verbose_name = 'Proveedor'

    def __str__(self):
        return self.empresa
