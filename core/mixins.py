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
