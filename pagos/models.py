# pagos/models.py
from django.db import models
from django.utils import timezone
from ventas.models import NotaVenta

class Pago(models.Model):
    """Modelo para almacenar la información de pagos procesados con Stripe."""
    
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido'),
        ('reembolsado', 'Reembolsado'),
    )
    
    nota_venta = models.OneToOneField(
        NotaVenta, 
        on_delete=models.CASCADE, 
        related_name='pago'
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Pago {self.id} - {self.nota_venta.id} - {self.estado}"
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-fecha_creacion']


class EventoStripe(models.Model):
    """Modelo para almacenar eventos de webhook de Stripe."""
    
    stripe_id = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=255)
    data = models.JSONField()
    procesado = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.stripe_id} - {self.type}"
    
    class Meta:
        verbose_name = "Evento Stripe"
        verbose_name_plural = "Eventos Stripe"
        ordering = ['-fecha_creacion']