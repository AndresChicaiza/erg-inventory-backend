from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    """Solo administradores."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.rol == 'Administrador')


class IsAdminOrReadOnly(BasePermission):
    """Lectura libre para autenticados; escritura solo para admin."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.rol == 'Administrador'


class IsAdminOrVendedor(BasePermission):
    """Admin o Vendedor pueden crear/editar."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.rol in ('Administrador', 'Vendedor'))


class IsAdminOrAlmacenista(BasePermission):
    """Admin o Almacenista pueden gestionar stock."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.rol in ('Administrador', 'Almacenista'))
