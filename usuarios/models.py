# usuarios/models.py
from django.db import models
from django.conf import settings # Para referenciar al User model de Django
from django.contrib.auth.models import Group

# Puedes crear los grupos/roles programáticamente o desde el admin de Django
# Ejemplo de cómo podrías asegurarte de que existan al iniciar:
def create_groups():
    Group.objects.get_or_create(name='Cliente')
    Group.objects.get_or_create(name='Vendedor')
    Group.objects.get_or_create(name='Reponedor')
    Group.objects.get_or_create(name='Administrador')
# Podrías llamar a create_groups() en un archivo de señales (signals.py) o en AppConfig.ready()

class Cliente(models.Model):
    # Vinculado uno a uno con el usuario de Django
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cliente_profile')
    nombre = models.CharField(max_length=100) # Podría autocompletarse desde User
    numero = models.CharField(max_length=30, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    points = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre or self.usuario.username

class Personal(models.Model):
    # Vinculado uno a uno con el usuario de Django
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='personal_profile')
    nombre = models.CharField(max_length=100) # Podría autocompletarse desde User
    # El cargo viene del Grupo al que pertenece el usuario
    # cargo = models.CharField(max_length=50) # Ya no es necesario aquí directamente

    def __str__(self):
        return self.nombre or self.usuario.username

    @property
    def cargo(self):
        # Devuelve el primer grupo (asumiendo un rol principal por usuario de personal)
        group = self.usuario.groups.first()
        return group.name if group else "Sin Cargo Asignado"