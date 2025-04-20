# inventario/models.py
from django.db import models
from productos.models import Producto # Importa el modelo Producto

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    ubicacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name_plural = "Sucursales"

class Stock(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='stock_items')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='stock_items')
    cantidad = models.PositiveIntegerField(default=0) # Usar PositiveIntegerField para asegurar >= 0

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en {self.sucursal.nombre}"

    class Meta:
        # Evita entradas duplicadas del mismo producto en la misma sucursal
        unique_together = ('producto', 'sucursal')
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"