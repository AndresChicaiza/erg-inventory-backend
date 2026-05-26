from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class AuditLog(models.Model):
    ACCIONES = (
        ('CREATE', 'Creación'),
        ('UPDATE', 'Modificación'),
        ('DELETE', 'Eliminación'),
        ('LOGIN',  'Inicio de Sesión'),
        ('LOGOUT', 'Cierre de Sesión'),
        ('EXPORT', 'Exportación'),
    )

    usuario     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    accion      = models.CharField(max_length=10, choices=ACCIONES)
    modulo      = models.CharField(max_length=50) # Ej: Facturación, Inventario
    modelo      = models.CharField(max_length=50) # Ej: Factura, Producto
    objeto_id   = models.CharField(max_length=50, blank=True, null=True)
    descripcion = models.TextField()
    cambios     = models.JSONField(null=True, blank=True) # Para guardar {campo: [viejo, nuevo]}
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    fecha       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'

    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.modelo} ({self.fecha})"
