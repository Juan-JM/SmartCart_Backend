# usuarios/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # Asegúrate que esta importación esté
from django.contrib.auth.models import User
from .models import Cliente, Personal

# 1. Define los Inlines primero (si los usas en UserAdmin)
class ClienteInline(admin.StackedInline):
    model = Cliente
    can_delete = False
    verbose_name_plural = 'Perfil Cliente'
    fk_name = 'usuario'
    fields = ('nombre', 'numero', 'direccion', 'points')
    readonly_fields = ('points',)

class PersonalInline(admin.StackedInline):
    model = Personal
    can_delete = False
    verbose_name_plural = 'Perfil Personal'
    fk_name = 'usuario'
    fields = ('nombre',)

# 2. Define tu clase UserAdmin personalizada *ANTES* de registrarla
class UserAdmin(BaseUserAdmin): # <---- DEFINICIÓN PRIMERO
    inlines = (ClienteInline, PersonalInline) # Usa los inlines definidos arriba
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_groups')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_groups(self, obj):
         return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = 'Grupos'

    # ... (Opcional: get_inline_instances si lo tenías) ...


# 3. Define los otros ModelAdmins (el decorador @admin.register ya los registra)
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'usuario_username', 'numero', 'points')
    search_fields = ['nombre', 'usuario__username', 'usuario__email', 'numero']
    list_filter = ('points',)
    autocomplete_fields = ['usuario']

    def usuario_username(self, obj):
        return obj.usuario.username
    usuario_username.short_description = 'Username'
    usuario_username.admin_order_field = 'usuario__username'

@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'usuario_username', 'cargo')
    search_fields = ['nombre', 'usuario__username']
    autocomplete_fields = ['usuario']

    def usuario_username(self, obj):
        return obj.usuario.username
    usuario_username.short_description = 'Username'
    usuario_username.admin_order_field = 'usuario__username'

    def cargo(self, obj):
        group = obj.usuario.groups.first()
        return group.name if group else "Sin Cargo"
    cargo.short_description = 'Cargo'


# 4. Registra explícitamente User usando tu clase UserAdmin *DESPUÉS* de definirla
admin.site.unregister(User) # Quita el registro por defecto
admin.site.register(User, UserAdmin) # <---- REGISTRO AL FINAL (usa la clase definida arriba)

# # usuarios/admin.py
# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# from django.contrib.auth.models import User
# from .models import Cliente, Personal

# # Define un inline admin descriptor para Cliente
# class ClienteInline(admin.StackedInline):
#     model = Cliente
#     can_delete = False
#     verbose_name_plural = 'Perfil Cliente'
#     fk_name = 'usuario'

# # Define un inline admin descriptor para Personal
# class PersonalInline(admin.StackedInline):
#     model = Personal
#     can_delete = False
#     verbose_name_plural = 'Perfil Personal'
#     fk_name = 'usuario'

# # Define un nuevo User admin
# class UserAdmin(BaseUserAdmin):
#     inlines = (ClienteInline, PersonalInline)
#     list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_groups')

#     def get_groups(self, obj):
#             return ", ".join([g.name for g in obj.groups.all()])
#     get_groups.short_description = 'Grupos'

#     def get_inline_instances(self, request, obj=None):
#         if not obj:
#             return list()
#         # Solo muestra el inline correspondiente si el perfil existe o si se está creando
#         # Puedes añadir lógica más compleja aquí si es necesario
#         return super().get_inline_instances(request, obj)


# # Re-register UserAdmin
# admin.site.unregister(User)
# admin.site.register(User, UserAdmin)

# # Registra los modelos independientes si quieres gestionarlos por separado (opcional)
# # admin.site.register(Cliente)
# # admin.site.register(Personal)