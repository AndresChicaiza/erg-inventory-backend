from .models import AuditLog

def log_action(user, action, modulo, modelo, objeto_id=None, descripcion="", cambios=None, request=None):
    """
    Registra una acción en el log de auditoría.
    """
    ip = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

    AuditLog.objects.create(
        usuario=user,
        accion=action,
        modulo=modulo,
        modelo=modelo,
        objeto_id=str(objeto_id) if objeto_id else None,
        descripcion=descripcion,
        cambios=cambios,
        ip_address=ip
    )
