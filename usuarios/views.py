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
    ChangePasswordSerializer, # NUEVO
    PermissionSerializer, 
    GroupDetailSerializer
)
from core.permissions import IsAdminOrReadOnly, IsClienteOwnerOrAdmin, IsVendedorOrAdmin, IsReponedorOrAdmin, IsCliente

from django.contrib.auth.models import Permission
from rest_framework import filters

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


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint para ver y editar grupos.
    """
    queryset = Group.objects.all().prefetch_related('permissions')
    serializer_class = GroupDetailSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para ver permisos (solo lectura).
    """
    queryset = Permission.objects.all().select_related('content_type')
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'codename', 'content_type__app_label', 'content_type__model']