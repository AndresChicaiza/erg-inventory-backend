from django.db import models

class Cliente(models.Model):
    TIPO_CHOICES   = [('Persona Natural', 'Persona Natural'), ('Corporativo', 'Corporativo')]
    ESTADO_CHOICES = [('Activo', 'Activo'), ('Inactivo', 'Inactivo')]

    nombre    = models.CharField(max_length=200)
    email     = models.EmailField(blank=True)
    telefono  = models.CharField(max_length=25, blank=True)
    tipo      = models.CharField(max_length=20, choices=TIPO_CHOICES, default='Persona Natural')
    ciudad    = models.CharField(max_length=100, blank=True)
    direccion = models.TextField(blank=True)
    estado    = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Activo')
    creado_en    = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clientes'
        ordering = ['nombre']
        verbose_name = 'Cliente'

    def __str__(self):
        return self.nombre
