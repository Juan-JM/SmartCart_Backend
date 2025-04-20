# core/permissions.py (o en usuarios/permissions.py)
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """ Permiso personalizado: Solo lectura para todos, escritura solo para Admin. """
    def has_permission(self, request, view):
        # Permisos de lectura (GET, HEAD, OPTIONS) para cualquiera.
        if request.method in permissions.SAFE_METHODS:
            return True
        # Permisos de escritura solo para usuarios administradores (is_staff).
        return request.user and request.user.is_staff

class IsClienteOwnerOrAdmin(permissions.BasePermission):
    """ Permiso para ver/editar perfil de cliente: solo el propio cliente o un admin. """
    def has_object_permission(self, request, view, obj):
        # Admin siempre tiene permiso
        if request.user and request.user.is_staff:
            return True
        # El usuario autenticado es el dueño del perfil de cliente
        return obj.usuario == request.user

class IsVendedorOrAdmin(permissions.BasePermission):
    """ Permiso para acciones de Vendedor o Administrador. """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
                (request.user.groups.filter(name__in=['Vendedor', 'Administrador']).exists() or request.user.is_staff)

class IsReponedorOrAdmin(permissions.BasePermission):
    """ Permiso para acciones de Reponedor o Administrador. """
    def has_permission(self, request, view):
            return request.user and request.user.is_authenticated and \
                (request.user.groups.filter(name__in=['Reponedor', 'Administrador']).exists() or request.user.is_staff)

# Puedes crear más permisos según necesites (ej. IsCliente for purchasing)
class IsCliente(permissions.BasePermission):
    """ Permiso para verificar si el usuario pertenece al grupo Cliente. """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and \
            request.user.groups.filter(name='Cliente').exists()