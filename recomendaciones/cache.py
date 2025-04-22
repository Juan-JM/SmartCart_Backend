# recomendaciones/cache.py
from django.core.cache import cache
from django.conf import settings
from productos.serializers import ProductoSerializer
from .models import ReglaAsociacion

class CacheRecomendaciones:
    """
    Sistema de cache para recomendaciones de productos.
    Almacena temporalmente recomendaciones para mejorar el rendimiento.
    """
    
    # Tiempo de expiración del cache en segundos (12 horas por defecto)
    CACHE_TIMEOUT = getattr(settings, 'RECOMENDACIONES_CACHE_TIMEOUT', 12 * 60 * 60)
    
    @staticmethod
    def obtener_clave_cache(producto_id):
        """Genera una clave única para el cache de un producto."""
        return f"recomendaciones_producto_{producto_id}"
    
    @classmethod
    def obtener_recomendaciones_cache(cls, producto_id, limite=5):
        """
        Intenta obtener recomendaciones desde el cache.
        
        Args:
            producto_id: ID del producto para el que se buscan recomendaciones
            limite: Número máximo de recomendaciones a retornar
            
        Returns:
            Lista de productos recomendados o None si no están en cache
        """
        clave = cls.obtener_clave_cache(producto_id)
        return cache.get(clave)
    
    @classmethod
    def guardar_recomendaciones_cache(cls, producto_id, recomendaciones):
        """
        Guarda recomendaciones en el cache.
        
        Args:
            producto_id: ID del producto origen
            recomendaciones: Lista de productos recomendados
        """
        clave = cls.obtener_clave_cache(producto_id)
        cache.set(clave, recomendaciones, cls.CACHE_TIMEOUT)
    
    @classmethod
    def invalidar_cache(cls, producto_id=None):
        """
        Invalida el cache de recomendaciones para un producto específico o todos.
        
        Args:
            producto_id: ID del producto a invalidar, o None para invalidar todo
        """
        if producto_id is not None:
            clave = cls.obtener_clave_cache(producto_id)
            cache.delete(clave)
        else:
            # Este método es menos eficiente pero sirve como ejemplo
            # En un sistema real, usaríamos un patrón para eliminar grupos de claves
            # o mantendríamos un registro de claves activas
            cache.clear()
    
    @classmethod
    def obtener_recomendaciones(cls, producto_id, limite=5, usar_cache=True, productos_excluir=None):
        """
        Obtiene recomendaciones para un producto, usando cache si está disponible.
        
        Args:
            producto_id: ID del producto origen
            limite: Número máximo de recomendaciones
            usar_cache: Si es False, fuerza recalcular aunque exista en cache
            productos_excluir: Lista de IDs de productos a excluir de las recomendaciones
            
        Returns:
            Lista de productos recomendados
        """
        productos_excluir = productos_excluir or []
        
        # Verificar cache si está habilitado
        if usar_cache:
            recomendaciones_cache = cls.obtener_recomendaciones_cache(producto_id)
            if recomendaciones_cache is not None:
                # Filtrar por productos excluidos y limitar
                recomendaciones_filtradas = [
                    r for r in recomendaciones_cache 
                    if r['id'] not in productos_excluir
                ][:limite]
                return recomendaciones_filtradas
        
        # Si no está en cache o no se usa cache, calcular
        reglas = ReglaAsociacion.objects.filter(
            producto_origen_id=producto_id
        ).exclude(
            producto_recomendado_id__in=productos_excluir
        ).select_related(
            'producto_recomendado'
        ).order_by('-lift', '-confianza')[:limite]
        
        # Convertir a formato serializado
        recomendaciones = []
        for regla in reglas:
            producto = regla.producto_recomendado
            recomendaciones.append({
                'id': producto.id,
                'producto': ProductoSerializer(producto).data,
                'puntuacion': regla.lift * regla.confianza,
                'confianza': regla.confianza,
                'lift': regla.lift
            })
        
        # Guardar en cache si hay recomendaciones
        if recomendaciones and usar_cache:
            cls.guardar_recomendaciones_cache(producto_id, recomendaciones)
        
        return recomendaciones