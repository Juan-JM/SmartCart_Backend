# productos/models.py
from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True) # Asegura nombres únicos

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    capacidad = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    #imagen
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)  # Opción recomendada

    # Relaciones ForeignKey
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True, related_name='productos')

    def __str__(self):
        return f"{self.nombre} ({self.marca})"

    class Meta:
         ordering = ['nombre'] # Ordenar por nombre por defecto