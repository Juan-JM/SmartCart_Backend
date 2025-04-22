# recomendaciones/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from celery.utils.log import get_task_logger

from .models import ConfiguracionRecomendacion
from .ml import GeneradorRecomendaciones
from .cache import CacheRecomendaciones

logger = get_task_logger(__name__)

@shared_task
def actualizar_recomendaciones():
    """
    Tarea Celery para actualizar periódicamente las recomendaciones.
    """
    try:
        logger.info("Iniciando actualización periódica de recomendaciones...")
        
        # Obtener configuración
        config, created = ConfiguracionRecomendacion.objects.get_or_create(pk=1)
        
        # Verificar si necesitamos actualizar (según frecuencia configurada)
        ejecutar = True
        if not created and config.ultima_actualizacion:
            dias_desde_ultima = (timezone.now() - config.ultima_actualizacion).days
            if dias_desde_ultima < config.frecuencia_actualizacion_dias:
                ejecutar = False
                logger.info(
                    f"La última actualización fue hace {dias_desde_ultima} días. "
                    f"Configurado para actualizar cada {config.frecuencia_actualizacion_dias} días. "
                    f"Saltando ejecución."
                )
        
        if ejecutar:
            # Ejecutar generador
            generador = GeneradorRecomendaciones()
            count = generador.generar_recomendaciones()
            
            if count is not None:
                logger.info(f"Se generaron {count} reglas de recomendación exitosamente.")
                
                # Limpiar cache de recomendaciones antiguas
                logger.info("Limpiando cache de recomendaciones...")
                CacheRecomendaciones.invalidar_cache()
                
                return f"Actualización completada: {count} reglas generadas."
            else:
                logger.error("Error al generar recomendaciones.")
                return "Error al generar recomendaciones."
        
        return "No es necesario actualizar las recomendaciones en este momento."
    
    except Exception as e:
        logger.error(f"Error en la tarea de actualización de recomendaciones: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"Error: {str(e)}"

@shared_task
def precalcular_recomendaciones_populares():
    """
    Tarea Celery para precalcular recomendaciones de productos populares.
    Esto mejora el rendimiento al tener las recomendaciones más comunes ya en cache.
    """
    from productos.models import Producto
    
    try:
        logger.info("Iniciando precálculo de recomendaciones para productos populares...")
        
        # Obtener los productos más populares (basado en ventas recientes, por ejemplo)
        # Esta lógica puede adaptarse según tu modelo de datos
        from django.db.models import Count
        from ventas.models import DetalleNotaVenta
        from datetime import timedelta
        
        # Productos más vendidos en el último mes
        fecha_limite = timezone.now() - timedelta(days=30)
        productos_populares = DetalleNotaVenta.objects.filter(
            nota_venta__fecha_hora__gte=fecha_limite
        ).values(
            'producto'
        ).annotate(
            total_vendidos=Count('producto')
        ).order_by('-total_vendidos')[:50]  # Top 50 productos
        
        productos_ids = [item['producto'] for item in productos_populares]
        
        # Para cada producto popular, precalcular y guardar en cache sus recomendaciones
        total_precalculados = 0
        for producto_id in productos_ids:
            recomendaciones = CacheRecomendaciones.obtener_recomendaciones(
                producto_id=producto_id,
                limite=10,  # Guardar más de las necesarias para tener margen
                usar_cache=False  # Forzar recálculo
            )
            
            if recomendaciones:
                total_precalculados += 1
        
        logger.info(f"Precálculo completado: {total_precalculados} productos con recomendaciones en cache.")
        return f"Precálculo completado: {total_precalculados} productos procesados."
    
    except Exception as e:
        logger.error(f"Error en precálculo de recomendaciones: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return f"Error: {str(e)}"

