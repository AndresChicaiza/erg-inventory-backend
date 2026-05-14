from .utils import log_action

class CreatedByMixin:
    """Guarda automáticamente quién creó el registro."""
    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)


class AuditMixin:
    """Registra automáticamente acciones en el log de auditoría."""
    
    def get_modulo_name(self):
        # Intenta obtener el nombre del módulo del view o del modelo
        return getattr(self, 'audit_modulo', self.__class__.__name__)

    def get_modelo_name(self):
        return getattr(self, 'audit_modelo', self.queryset.model.__name__ if hasattr(self, 'queryset') else 'Desconocido')

    def perform_create(self, serializer):
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='CREATE',
            modulo=self.get_modulo_name(),
            modelo=self.get_modelo_name(),
            objeto_id=instance.id,
            descripcion=f"Creado nuevo registro: {instance}",
            request=self.request
        )

    def perform_update(self, serializer):
        # Capturar datos viejos para el log de cambios (opcional/avanzado)
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='UPDATE',
            modulo=self.get_modulo_name(),
            modelo=self.get_modelo_name(),
            objeto_id=instance.id,
            descripcion=f"Actualizado registro: {instance}",
            request=self.request
        )

    def perform_destroy(self, instance):
        obj_id = instance.id
        obj_str = str(instance)
        instance.delete()
        log_action(
            user=self.request.user,
            action='DELETE',
            modulo=self.get_modulo_name(),
            modelo=self.get_modelo_name(),
            objeto_id=obj_id,
            descripcion=f"Eliminado registro: {obj_str}",
            request=self.request
        )

from rest_framework.exceptions import ValidationError
from datetime import date

class CheckCierreMixin:
    """Evita modificación o eliminación de registros anteriores al cierre contable."""
    
    def get_fecha_registro(self, instance):
        # Sobrescribir en las vistas si el campo de fecha es distinto
        if hasattr(instance, 'fecha_emision'): return instance.fecha_emision
        if hasattr(instance, 'fecha_registro'): return instance.fecha_registro
        if hasattr(instance, 'fecha_pago'): return instance.fecha_pago
        if hasattr(instance, 'creado_en'): return instance.creado_en.date()
        return None

    def check_cierre(self, fecha):
        if not fecha: return
        from configuracion.models import ConfiguracionEmpresa
        config = ConfiguracionEmpresa.objects.first()
        if config and config.fecha_cierre_contable:
            if isinstance(fecha, date):
                # Ensure we only compare dates, not datetimes
                if type(fecha) is not date:
                    fecha = fecha.date()
                if fecha <= config.fecha_cierre_contable:
                    raise ValidationError(f"No se pueden modificar registros del período cerrado (antes o igual a {config.fecha_cierre_contable})")

    def perform_update(self, serializer):
        # Chequear la fecha del registro antes de actualizar
        self.check_cierre(self.get_fecha_registro(serializer.instance))
        
        # También chequear si se intenta cambiar la fecha a una cerrada
        nueva_fecha = None
        data = serializer.validated_data
        if 'fecha_emision' in data: nueva_fecha = data['fecha_emision']
        elif 'fecha_registro' in data: nueva_fecha = data['fecha_registro']
        elif 'fecha_pago' in data: nueva_fecha = data['fecha_pago']
        
        if nueva_fecha:
            self.check_cierre(nueva_fecha)
            
        super().perform_update(serializer)

    def perform_destroy(self, instance):
        self.check_cierre(self.get_fecha_registro(instance))
        super().perform_destroy(instance)
