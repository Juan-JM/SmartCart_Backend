# recomendaciones/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from .models import ReglaAsociacion, ConfiguracionRecomendacion
from .serializers import ReglaAsociacionSerializer, ConfiguracionRecomendacionSerializer
from productos.models import Producto
from productos.serializers import ProductoSerializer
from core.permissions import IsAdminOrReadOnly
from django.core.cache import cache

class ReglaAsociacionViewSet(viewsets.ModelViewSet):
    queryset = ReglaAsociacion.objects.all()
    serializer_class = ReglaAsociacionSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    # Solo para depuración - en producción las reglas se generan automáticamente
    
class ConfiguracionRecomendacionViewSet(viewsets.ModelViewSet):
    queryset = ConfiguracionRecomendacion.objects.all()
    serializer_class = ConfiguracionRecomendacionSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_object(self):
        """Siempre retorna la primera configuración o crea una si no existe."""
        config, created = ConfiguracionRecomendacion.objects.get_or_create(pk=1)
        return config

class RecomendacionesAPIView(APIView):
    """API para obtener recomendaciones basadas en los productos en el carrito."""
    permission_classes = [permissions.AllowAny]  # Cualquiera puede acceder a recomendaciones
    
    def post(self, request, *args, **kwargs):
        productos_carrito = request.data.get('productos', [])
        limite = request.data.get('limite', 3)
        
        if not productos_carrito:
            return Response({"detail": "No se especificaron productos."}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Generar clave única para este conjunto de productos (para cache)
        productos_key = "_".join(sorted([str(id) for id in productos_carrito]))
        cache_key = f"recomendaciones_carrito_{productos_key}_limite_{limite}"
        
        # Intentar obtener del cache
        recomendaciones_cache = cache.get(cache_key)
        if recomendaciones_cache is not None:
            return Response(recomendaciones_cache)
        
        # Si no está en cache, obtener recomendaciones
        recomendaciones = self._obtener_recomendaciones_para_carrito(productos_carrito, limite)
        
        # Guardar en cache por 1 hora (3600 segundos)
        cache.set(cache_key, recomendaciones, 3600)
        
        return Response(recomendaciones)
    
    def _obtener_recomendaciones_para_carrito(self, ids_productos_carrito, limite=3):
        """
        Obtiene recomendaciones basadas en los productos del carrito.
        
        Args:
            ids_productos_carrito: Lista de IDs de productos en el carrito
            limite: Número máximo de recomendaciones por producto
            
        Returns:
            Lista de productos recomendados con sus puntuaciones
        """
        # Conjunto para evitar recomendar productos que ya están en el carrito
        productos_excluir = set(ids_productos_carrito)
        todas_recomendaciones = {}
        
        # Para cada producto en el carrito, buscamos sus recomendaciones
        for producto_id in ids_productos_carrito:
            # Obtener reglas de asociación donde este producto es el origen
            reglas = ReglaAsociacion.objects.filter(
                producto_origen_id=producto_id
            ).exclude(
                # Excluir productos que ya están en el carrito
                producto_recomendado_id__in=productos_excluir
            ).select_related(
                'producto_recomendado'
            ).order_by('-lift', '-confianza')[:limite*2]  # Obtenemos más para tener margen
            
            # Agregamos los productos recomendados al diccionario de todas las recomendaciones
            for regla in reglas:
                producto = regla.producto_recomendado
                if producto.id not in todas_recomendaciones:
                    todas_recomendaciones[producto.id] = {
                        'producto': ProductoSerializer(producto).data,
                        'puntuacion': regla.lift * regla.confianza,  # Puntuación combinada
                        'frecuencia': 1
                    }
                else:
                    # Si ya existe, incrementamos su puntuación y frecuencia
                    todas_recomendaciones[producto.id]['puntuacion'] += regla.lift * regla.confianza
                    todas_recomendaciones[producto.id]['frecuencia'] += 1
        
        # Ordenar por puntuación/frecuencia (promedio) y limitar
        recomendaciones_ordenadas = sorted(
            todas_recomendaciones.values(),
            key=lambda x: x['puntuacion'] / x['frecuencia'],
            reverse=True
        )[:limite]
        
        return recomendaciones_ordenadas