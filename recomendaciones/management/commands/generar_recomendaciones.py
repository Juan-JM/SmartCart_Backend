# recomendaciones/management/commands/generar_recomendaciones.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ...models import ConfiguracionRecomendacion
from ...ml import GeneradorRecomendaciones

class Command(BaseCommand):
    help = 'Genera recomendaciones de productos utilizando el algoritmo Apriori'

    def handle(self, *args, **options):
        # Obtener configuración
        config, created = ConfiguracionRecomendacion.objects.get_or_create(pk=1)
        
        # Verificar si necesitamos actualizar (según frecuencia configurada)
        ejecutar = True
        if not created and config.ultima_actualizacion:
            dias_desde_ultima = (timezone.now() - config.ultima_actualizacion).days
            if dias_desde_ultima < config.frecuencia_actualizacion_dias:
                ejecutar = False
                self.stdout.write(
                    self.style.WARNING(
                        f"La última actualización fue hace {dias_desde_ultima} días. "
                        f"Configurado para actualizar cada {config.frecuencia_actualizacion_dias} días. "
                        f"Saltando ejecución."
                    )
                )
        
        if ejecutar:
            self.stdout.write(self.style.NOTICE("Iniciando generación de recomendaciones..."))
            
            # Ejecutar generador
            generador = GeneradorRecomendaciones()
            count = generador.generar_recomendaciones()
            
            if count is not None:
                self.stdout.write(
                    self.style.SUCCESS(f"Se generaron {count} reglas de recomendación exitosamente.")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("Error al generar recomendaciones.")
                )
        
        return