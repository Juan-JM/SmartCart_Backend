# ventas/views.py
from rest_framework import viewsets, permissions, generics
from .models import NotaVenta, DetalleNotaVenta
from .serializers import NotaVentaSerializer, DetalleNotaVentaSerializer
from core.permissions import IsVendedorOrAdmin, IsCliente, IsAdminOrReadOnly

class NotaVentaViewSet(viewsets.ModelViewSet):
    serializer_class = NotaVentaSerializer

    def get_queryset(self):
        """ Filtra las ventas: Admins/Vendedores ven todas, Clientes solo las suyas. """
        user = self.request.user
        if user.is_staff or user.groups.filter(name='Vendedor').exists():
            return NotaVenta.objects.select_related('cliente__usuario').prefetch_related('detalles__producto').all()
        elif hasattr(user, 'cliente_profile'): # Si es un cliente
                return NotaVenta.objects.filter(cliente=user.cliente_profile).select_related('cliente__usuario').prefetch_related('detalles__producto')
        return NotaVenta.objects.none() # No mostrar nada si no es ninguno de los anteriores

    def get_permissions(self):
        """ Define permisos por acción. """
        if self.action in ['list', 'retrieve']:
            # Clientes pueden ver sus ventas, Vendedores/Admins pueden ver todas
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'create':
                # Clientes o Vendedores/Admins pueden crear ventas
                permission_classes = [IsCliente | IsVendedorOrAdmin] # '|' significa OR
        elif self.action in ['update', 'partial_update', 'destroy']:
                # Solo Admins pueden modificar/borrar ventas (generalmente no se borran)
                permission_classes = [permissions.IsAdminUser]
        else:
                permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """ Asigna el cliente automáticamente si el usuario es un Cliente. """
        user = self.request.user
        cliente_profile = getattr(user, 'cliente_profile', None)
        # Si el usuario es cliente y no se especificó un cliente_id, se asigna él mismo.
        # Si es Vendedor/Admin, DEBE especificar cliente_id (o dejarlo null para consumidor final).
        if cliente_profile and 'cliente_id' not in serializer.validated_data:
                serializer.save(cliente=cliente_profile)
        else:
                # Permite que Vendedor/Admin asignen cliente_id o lo dejen null
                serializer.save()

# Generalmente no expones DetalleNotaVenta directamente, se maneja a través de NotaVenta
# Pero si lo necesitas (ej. para reportes específicos):
# class DetalleNotaVentaViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = DetalleNotaVenta.objects.select_related('nota_venta', 'producto').all()
#     serializer_class = DetalleNotaVentaSerializer
#     permission_classes = [IsVendedorOrAdmin] # Solo personal interno ve detalles sueltos?
