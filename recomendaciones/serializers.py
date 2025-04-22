# recomendaciones/serializers.py
from rest_framework import serializers
from .models import ReglaAsociacion, ConfiguracionRecomendacion
from productos.serializers import ProductoSerializer

class ReglaAsociacionSerializer(serializers.ModelSerializer):
    producto_recomendado_detalle = ProductoSerializer(source='producto_recomendado', read_only=True)
    
    class Meta:
        model = ReglaAsociacion
        fields = ('id', 'producto_origen', 'producto_recomendado', 'producto_recomendado_detalle',
                  'soporte', 'confianza', 'lift', 'ultima_actualizacion')

class ConfiguracionRecomendacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionRecomendacion
        fields = '__all__'
