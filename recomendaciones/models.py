# recomendaciones/models.py
from django.db import models
from productos.models import Producto

class ReglaAsociacion(models.Model):
    """Modelo para almacenar reglas de asociación entre productos."""
    producto_origen = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE, 
        related_name='reglas_origen'
    )
    producto_recomendado = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE, 
        related_name='reglas_recomendado'
    )
    soporte = models.FloatField(
        help_text="Frecuencia de aparición del conjunto en el total de transacciones"
    )
    confianza = models.FloatField(
        help_text="Probabilidad de que el producto recomendado aparezca cuando aparece el origen"
    )
    lift = models.FloatField(
        help_text="Relación entre la confianza y la frecuencia esperada del producto recomendado"
    )
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('producto_origen', 'producto_recomendado')
        ordering = ['-lift', '-confianza']
        verbose_name = "Regla de Asociación"
        verbose_name_plural = "Reglas de Asociación"
        
        # Añadir índices para mejorar rendimiento de consultas
        indexes = [
            models.Index(fields=['producto_origen', '-lift', '-confianza']),
            models.Index(fields=['producto_recomendado']),
        ]

    def __str__(self):
        return f"{self.producto_origen.nombre} → {self.producto_recomendado.nombre} (conf: {self.confianza:.2f}, lift: {self.lift:.2f})"

class ConfiguracionRecomendacion(models.Model):
    """Configuración para el algoritmo de recomendaciones."""
    soporte_minimo = models.FloatField(default=0.01)
    confianza_minima = models.FloatField(default=0.2)
    lift_minimo = models.FloatField(default=1.0)
    max_recomendaciones = models.PositiveIntegerField(default=5)
    frecuencia_actualizacion_dias = models.PositiveIntegerField(default=7)
    ultima_actualizacion = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Configuración de Recomendaciones (actualizado: {self.ultima_actualizacion})"