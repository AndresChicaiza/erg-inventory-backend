from rest_framework.permissions import BasePermission, SAFE_METHODS


# ── Helpers ─────────────────────────────────────────────────────────────────

def _rol(request, *roles):
    return (
        request.user
        and request.user.is_authenticated
        and request.user.rol in roles
    )

ADMIN       = ('Administrador',)
ADMIN_CONTA = ('Administrador', 'Contador')
ADMIN_CONTA_VEND = ('Administrador', 'Contador', 'Vendedor')
LOGISTICA   = ('Logistica',)
JEFE_FAB    = ('JefeFabrica',)
BODEGUERO   = ('Bodeguero',)
RRHH        = ('RRHH',)

ADMIN_CONTA_VEND_LOG = ('Administrador', 'Contador', 'Vendedor', 'Logistica')
ADMIN_CONTA_VEND_LOG_BOD_JEFE = ('Administrador', 'Contador', 'Vendedor', 'Logistica', 'Bodeguero', 'JefeFabrica')
ADMIN_CONTA_VEND_BOD_JEFE = ('Administrador', 'Contador', 'Vendedor', 'Bodeguero', 'JefeFabrica')


# ── Permisos básicos ─────────────────────────────────────────────────────────

class IsAdmin(BasePermission):
    """Solo Administrador."""
    def has_permission(self, request, view):
        return _rol(request, *ADMIN)


class IsAdminOrContador(BasePermission):
    """Administrador o Contador."""
    def has_permission(self, request, view):
        return _rol(request, *ADMIN_CONTA)


class IsAdminOrReadOnly(BasePermission):
    """Lectura para todos los autenticados; escritura solo Admin o Contador."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return _rol(request, *ADMIN_CONTA)


# ── Productos ────────────────────────────────────────────────────────────────

class CanCreateProducto(BasePermission):
    """Admin, Contador, JefeFabrica pueden crear."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return _rol(request, 'Administrador', 'Contador', 'JefeFabrica')

class CanSubirProductoFinal(BasePermission):
    """Admin, Contador, Logística y JefeFabrica suben productos terminados al inventario."""
    def has_permission(self, request, view):
        return _rol(request, 'Administrador', 'Contador', 'Logistica', 'JefeFabrica')


# ── Bodegas ──────────────────────────────────────────────────────────────────

class CanCreateBodega(BasePermission):
    """Solo Admin y Contador crean/editan bodegas."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return _rol(request, *ADMIN_CONTA)


# ── Ventas / Facturas ────────────────────────────────────────────────────────

class CanCreateVenta(BasePermission):
    """Admin, Contador y Vendedor crean ventas."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated): return False
        if request.method in SAFE_METHODS: return _rol(request, *ADMIN_CONTA_VEND)
        return _rol(request, *ADMIN_CONTA_VEND)


class CanEmitirFactura(BasePermission):
    """Admin, Contador y Vendedor emiten facturas."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated): return False
        if request.method in SAFE_METHODS: return _rol(request, *ADMIN_CONTA_VEND)
        return _rol(request, *ADMIN_CONTA_VEND)

class CanCreateCliente(BasePermission):
    """Admin, Contador y Vendedor pueden crear/editar clientes."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated): return False
        if request.method in SAFE_METHODS: return True
        return _rol(request, *ADMIN_CONTA_VEND)


# ── Órdenes de Compra ────────────────────────────────────────────────────────

class CanCreateOC(BasePermission):
    """
    Vendedor: OC de productos de tienda
    Bodeguero y JefeFabrica: OC de materias primas
    Admin y Contador: cualquier OC
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated): return False
        if request.method in SAFE_METHODS: return True
        return _rol(
            request,
            'Administrador', 'Contador',
            'Vendedor', 'Bodeguero', 'JefeFabrica'
        )


class CanAprobarOC(BasePermission):
    """Solo Admin y Contador aprueban OC."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated): return False
        if request.method in SAFE_METHODS: return True
        return _rol(request, *ADMIN_CONTA)


class CanRecibirOC(BasePermission):
    """
    Vendedor recibe OC de tienda.
    Bodeguero y JefeFabrica reciben OC de MP/bodega.
    """
    def has_permission(self, request, view):
        return _rol(
            request,
            'Administrador', 'Contador',
            'Vendedor', 'Bodeguero', 'JefeFabrica'
        )


# ── Inventario / Movimientos ─────────────────────────────────────────────────

class CanMovimientoInventario(BasePermission):
    """Logística y Vendedor (su sede) hacen movimientos."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated): return False
        if request.method in SAFE_METHODS: return True
        return _rol(
            request,
            'Administrador', 'Contador',
            'Logistica', 'Vendedor', 'Bodeguero', 'JefeFabrica'
        )


# ── Logística ────────────────────────────────────────────────────────────────

class CanEditEnvio(BasePermission):
    """Solo Logística y Admin editan estados de envío."""
    def has_permission(self, request, view):
        return _rol(request, 'Administrador', 'Logistica')


# ── RRHH / Nómina ────────────────────────────────────────────────────────────

class CanManageRRHH(BasePermission):
    """Admin, Contador y RRHH gestionan empleados y nómina."""
    def has_permission(self, request, view):
        return _rol(request, 'Administrador', 'Contador', 'RRHH')


# ── Configuración ────────────────────────────────────────────────────────────

class CanEditConfiguracion(BasePermission):
    """Solo Admin edita la configuración del sistema."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return _rol(request, *ADMIN_CONTA)
        return _rol(request, *ADMIN)


# ── Trazabilidad mixin (para views) ──────────────────────────────────────────

class AuditMixin:
    """
    Agrega creado_por y modificado_por automáticamente.
    Usar en views que hereden de generics.*
    """
    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)

    def perform_update(self, serializer):
        serializer.save(modificado_por=self.request.user)