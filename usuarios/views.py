# usuarios/views.py
from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User, Group
from .models import Cliente, Personal
from .serializers import (
    BaseUserSerializer, # Cambiado de UserSerializer a BaseUserSerializer
    RegisterSerializer,
    ClienteSerializer, # Mantenemos ClienteSerializer para el ViewSet de Cliente
    PersonalSerializer, # Mantenemos PersonalSerializer para el ViewSet de Personal
    UserProfileSerializer, # NUEVO
    ChangePasswordSerializer # NUEVO
)
from core.permissions import IsAdminOrReadOnly, IsClienteOwnerOrAdmin, IsVendedorOrAdmin, IsReponedorOrAdmin, IsCliente

# --- Vistas existentes (revisadas/actualizadas) ---

class RegistrationAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all().order_by('id').prefetch_related('groups') # prefetch_related para groups
    serializer_class = BaseUserSerializer # Usar el serializer base
    permission_classes = [permissions.IsAdminUser]

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related('usuario').all()
    serializer_class = ClienteSerializer # Usar ClienteSerializer aquí

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsVendedorOrAdmin]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsClienteOwnerOrAdmin] # El permiso verifica obj.usuario == request.user
        elif self.action == 'create':
             permission_classes = [permissions.IsAdminUser]
        elif self.action == 'destroy':
             permission_classes = [permissions.IsAdminUser]
        else:
             permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]

    # No permitir que un cliente se cree a sí mismo desde aquí
    # def perform_create(self, serializer):
    #     serializer.save() # Admins crean clientes


class PersonalViewSet(viewsets.ModelViewSet):
    queryset = Personal.objects.select_related('usuario').prefetch_related('usuario__groups').all() # Añadir groups
    serializer_class = PersonalSerializer # Usar PersonalSerializer
    permission_classes = [permissions.IsAdminUser]


# --- VISTAS ACTUALIZADAS ---

class UserProfileAPIView(generics.RetrieveUpdateAPIView):

    serializer_class = UserProfileSerializer # Usar el nuevo serializer combinado
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Optimizar la consulta para cargar relaciones necesarias
        user = User.objects.filter(pk=self.request.user.pk).prefetch_related(
            'groups__permissions',
            'user_permissions',
            'cliente_profile',
            'personal_profile'
        ).first()
        return user

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
        # user = User.objects.select_related(
        #     'cliente_profile' # Usar el related_name
        #  ).prefetch_related(
        #      'groups' # Asegurar que los grupos estén disponibles
        #  ).get(pk=self.request.user.pk)

        # # Añadir el perfil de personal si existe (generalmente solo para staff)
        # if hasattr(self.request.user, 'personal_profile'):
        #      user = User.objects.select_related(
        #          'personal_profile'
        #      ).prefetch_related(
        #          'groups'
        #      ).get(pk=self.request.user.pk)

        # return user


class ChangePasswordAPIView(generics.UpdateAPIView):
    """
    Vista para que el usuario autenticado cambie su contraseña.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True) # Valida old_password, new_password, new_password_confirm

        # Si la validación es exitosa, actualiza la contraseña
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        return Response({"message": "Contraseña actualizada con éxito."}, status=status.HTTP_200_OK)



# # usuarios/views.py
# from rest_framework import generics, viewsets, permissions, status
# from rest_framework.response import Response
# from django.contrib.auth.models import User, Group
# from .models import Cliente, Personal
# from .serializers import UserSerializer, RegisterSerializer, ClienteSerializer, PersonalSerializer
# # Importa tus permisos personalizados
# from core.permissions import IsAdminOrReadOnly, IsClienteOwnerOrAdmin, IsVendedorOrAdmin, IsReponedorOrAdmin, IsCliente

# class RegistrationAPIView(generics.CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = RegisterSerializer
#     permission_classes = [permissions.AllowAny] # Cualquiera puede registrarse

# class UserViewSet(viewsets.ReadOnlyModelViewSet): # Solo lectura para usuarios generales
#     queryset = User.objects.all().order_by('id')
#     serializer_class = UserSerializer
#     # Solo Admins pueden listar/ver todos los usuarios
#     permission_classes = [permissions.IsAdminUser]

# class ClienteViewSet(viewsets.ModelViewSet):
#     queryset = Cliente.objects.select_related('usuario').all() # Optimizar consulta
#     serializer_class = ClienteSerializer

#     def get_permissions(self):
#         """ Asignar permisos basados en la acción. """
#         if self.action in ['list', 'retrieve']:
#             # Admins o Vendedores pueden ver clientes
#             permission_classes = [IsVendedorOrAdmin]
#         elif self.action in ['update', 'partial_update']:
#                 # Solo el propio cliente o un admin pueden editar
#             permission_classes = [IsClienteOwnerOrAdmin]
#         elif self.action == 'create':
#                 # La creación se maneja en Registration o por Admins
#                 permission_classes = [permissions.IsAdminUser]
#         elif self.action == 'destroy':
#                 # Solo Admins pueden borrar
#                 permission_classes = [permissions.IsAdminUser]
#         else:
#                 permission_classes = [permissions.IsAdminUser] # Por defecto, restringir
#         return [permission() for permission in permission_classes]

# class PersonalViewSet(viewsets.ModelViewSet):
#     queryset = Personal.objects.select_related('usuario').all()
#     serializer_class = PersonalSerializer
#     # Solo Admins pueden gestionar al personal
#     permission_classes = [permissions.IsAdminUser]

# class UserProfileAPIView(generics.RetrieveUpdateAPIView):
#         """ Vista para que el usuario autenticado vea/edite su propio perfil. """
#         serializer_class = UserSerializer # Podrías necesitar un serializer específico para el perfil
#         permission_classes = [permissions.IsAuthenticated]

#         def get_object(self):
#             # Devuelve el perfil del usuario autenticado
#             return self.request.user

#         # Opcionalmente, podrías querer unificar la vista del perfil User y Cliente/Personal
#         # Esto requeriría un serializer más complejo o lógica adicional en la vista.

# # Vista para cambiar contraseña (ejemplo básico)
# class ChangePasswordAPIView(generics.UpdateAPIView):
#     serializer_class = serializers.Serializer # Usa un serializer específico para cambio de contraseña
#     permission_classes = [permissions.IsAuthenticated]

#     def update(self, request, *args, **kwargs):
#         user = request.user
#         # Aquí iría la lógica para validar la contraseña actual y establecer la nueva
#         # Necesitarás crear un ChangePasswordSerializer
#         # ... (lógica de cambio de contraseña) ...
#         return Response({"message": "Contraseña actualizada con éxito."}, status=status.HTTP_200_OK)
