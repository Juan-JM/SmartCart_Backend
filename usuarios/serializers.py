# usuarios/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate # Para validar contraseña antigua
from django.db import transaction
from .models import Cliente, Personal
from django.contrib.auth.models import Permission, ContentType

# --- Serializers existentes (revisados/confirmados) ---

class GroupSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ('name', 'permissions')

    def get_permissions(self, obj):
        request = self.context.get('request')
        if request and request.user.is_staff:
            return [f"{perm.content_type.app_label}.{perm.codename}" for perm in obj.permissions.all()]
        return None

# Serializer base para User (solo lectura en la mayoría de los casos)
class BaseUserSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'groups', 'is_staff', 'is_active')
        read_only_fields = ('id', 'username', 'groups', 'is_staff', 'is_active') # Campos que un usuario normal no debería poder cambiar directamente aquí

# Serializer para el perfil Cliente (lectura y potencialmente escritura de sus campos)
class ClienteSerializer(serializers.ModelSerializer):
    # No incluimos 'usuario' aquí para evitar redundancia si se anida
    class Meta:
        model = Cliente
        fields = ('id','nombre', 'numero', 'direccion', 'points', 'usuario_id')
        read_only_fields = ('id','points',)

# Serializer para el perfil Personal (solo lectura)
class PersonalSerializer(serializers.ModelSerializer):
    cargo = serializers.CharField(read_only=True)
    class Meta:
        model = Personal
        fields = ('nombre', 'cargo')
        read_only_fields = fields # El perfil de personal no se edita por el propio usuario generalmente


# --- NUEVO: Serializer para el Perfil Completo del Usuario (User + Cliente/Personal) ---
class UserProfileSerializer(serializers.ModelSerializer):
    cliente_profile = ClienteSerializer(required=False)
    personal_profile = PersonalSerializer(read_only=True, required=False)
    groups = serializers.SerializerMethodField()
    user_permissions = serializers.SerializerMethodField()
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser',
                  'groups', 'user_permissions', 'cliente_profile', 'personal_profile')
        read_only_fields = ('id', 'username', 'is_staff', 'is_superuser')

    def get_groups(self, obj):
        groups = obj.groups.all()
        serializer = GroupSerializer(groups, many=True, context=self.context)
        return serializer.data

    def get_user_permissions(self, obj):
        if obj.is_staff:
            return [f"{perm.content_type.app_label}.{perm.codename}" for perm in obj.user_permissions.all()]
        return None
    
    def get_context(self):
        # Pasar contexto al GroupSerializer para determinar si mostrar permisos
        context = super().get_context()
        if context is None:
            context = {}
        context['show_permissions'] = self.instance.is_staff if self.instance else False
        return context
    def update(self, instance, validated_data):
        # Extraer datos del perfil de cliente si existen
        cliente_data = validated_data.pop('cliente_profile', None)
        groups_data = validated_data.pop('groups', None)

        # Actualizar campos del User
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        
        # Actualizar grupos si se proporcionan
        if groups_data is not None and self.context['request'].user.is_staff:
            instance.groups.set(groups_data)
        
        instance.save()

        # Actualizar campos del Cliente si existen datos y el perfil existe
        if cliente_data and hasattr(instance, 'cliente_profile'):
            cliente_serializer = ClienteSerializer(instance.cliente_profile, data=cliente_data, partial=True)
            if cliente_serializer.is_valid(raise_exception=True):
                cliente_serializer.save()

        return instance    
    # def update(self, instance, validated_data):
    #     # Extraer datos del perfil de cliente si existen
    #     cliente_data = validated_data.pop('cliente_profile', None)

    #     # Actualizar campos del User (email, first_name, last_name)
    #     instance.email = validated_data.get('email', instance.email)
    #     instance.first_name = validated_data.get('first_name', instance.first_name)
    #     instance.last_name = validated_data.get('last_name', instance.last_name)
    #     instance.save()

    #     # Actualizar campos del Cliente si existen datos y el perfil existe
    #     # Usamos hasattr para verificar si el usuario tiene un perfil de cliente
    #     if cliente_data and hasattr(instance, 'cliente_profile'):
    #         cliente_serializer = ClienteSerializer(instance.cliente_profile, data=cliente_data, partial=True)
    #         if cliente_serializer.is_valid(raise_exception=True):
    #             cliente_serializer.save()
    #     # No se actualiza el perfil de Personal aquí (se asume gestión por Admin)

    #     return instance

# --- NUEVO: Serializer para Cambiar Contraseña ---
class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para el cambio de contraseña.
    """
    old_password = serializers.CharField(required=True, write_only=True, label="Contraseña Antigua")
    new_password = serializers.CharField(required=True, write_only=True, label="Nueva Contraseña", validators=[validate_password]) # Aplica validadores de Django
    new_password_confirm = serializers.CharField(required=True, write_only=True, label="Confirmar Nueva Contraseña")

    def validate_old_password(self, value):
        """
        Valida que la contraseña antigua sea correcta.
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña antigua no es correcta.")
        return value

    def validate(self, data):
        """
        Valida que las nuevas contraseñas coincidan.
        """
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Las nuevas contraseñas no coinciden."})
        # Puedes añadir validación extra aquí si es necesario (ej. no igual a la antigua)
        if data['old_password'] == data['new_password']:
             raise serializers.ValidationError({"new_password": "La nueva contraseña no puede ser igual a la anterior."})
        return data

    # No necesitamos un método create, ya que es una actualización
    # Podríamos añadir un método save si quisiéramos encapsular la lógica de cambio aquí,
    # pero es más común hacerlo en la vista para este caso.


# --- Serializer de Registro (confirmado/sin cambios necesarios por ahora) ---
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirmar Contraseña")
    nombre_cliente = serializers.CharField(write_only=True, required=True, max_length=100)
    numero = serializers.CharField(write_only=True, required=False, allow_blank=True, max_length=30)
    direccion = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name',
                  'nombre_cliente', 'numero', 'direccion')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        # Eliminar password2 ya que no se guarda en el modelo User
        attrs.pop('password2')
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Extraer datos del cliente antes de crear el User
        nombre_cliente = validated_data.pop('nombre_cliente')
        numero = validated_data.pop('numero', None)
        direccion = validated_data.pop('direccion', None)

        # Crear el usuario
        user = User.objects.create_user( # Usar create_user para hashear contraseña
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'], # create_user maneja el hash
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        # Asignar al grupo 'Cliente'
        cliente_group, created = Group.objects.get_or_create(name='Cliente')
        user.groups.add(cliente_group)
        # user.save() # create_user ya guarda el usuario

        # Crear el perfil Cliente
        Cliente.objects.create(
            usuario=user,
            nombre=nombre_cliente,
            numero=numero,
            direccion=direccion
        )
        return user


class PermissionSerializer(serializers.ModelSerializer):
    content_type_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Permission
        fields = ('id', 'name', 'codename', 'content_type', 'content_type_name')
    
    def get_content_type_name(self, obj):
        return f"{obj.content_type.app_label}.{obj.content_type.model}"

class GroupDetailSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=False)
    
    class Meta:
        model = Group
        fields = ('id', 'name', 'permissions')
    
    def create(self, validated_data):
        permissions_data = validated_data.pop('permissions', [])
        group = Group.objects.create(**validated_data)
        
        if permissions_data:
            permission_ids = [permission['id'] for permission in permissions_data]
            group.permissions.set(Permission.objects.filter(id__in=permission_ids))
        
        return group
    
    def update(self, instance, validated_data):
        permissions_data = validated_data.pop('permissions', [])
        
        # Update group name
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        
        # Update permissions if provided
        if permissions_data:
            permission_ids = [permission['id'] for permission in permissions_data]
            instance.permissions.set(Permission.objects.filter(id__in=permission_ids))
        
        return instance