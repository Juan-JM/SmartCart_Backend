# ventas/models.py
from django.db import models
from django.utils import timezone # Para manejar fechas y horas
from usuarios.models import Cliente
from productos.models import Producto

class NotaVenta(models.Model):
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='notas_venta')
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fecha_hora = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    
    def __str__(self):
        cliente_nombre = self.cliente.nombre if self.cliente else "Consumidor Final"
        return f"Venta #{self.id} - {cliente_nombre} - {self.fecha_hora.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-fecha_hora'] # Ordenar por fecha más reciente
        verbose_name = "Nota de Venta"
        verbose_name_plural = "Notas de Venta"

class DetalleNotaVenta(models.Model):
    nota_venta = models.ForeignKey(NotaVenta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_venta') # PROTECT para no borrar producto si está en una venta
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2) # Guardar el precio al momento de la venta
    subtotal = models.DecimalField(max_digits=10, decimal_places=2) # Calculado: cantidad * precio_unitario

    def save(self, *args, **kwargs):
        # Calcula el subtotal antes de guardar
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        # Podrías añadir lógica para actualizar el monto_total de NotaVenta aquí o con señales

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} @ {self.precio_unitario}"

    class Meta:
        verbose_name = "Detalle de Nota de Venta"
        verbose_name_plural = "Detalles de Notas de Venta"