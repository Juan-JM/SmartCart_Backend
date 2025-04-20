# inventario/serializers.py
from rest_framework import serializers
from .models import Sucursal, Stock
from productos.serializers import ProductoSerializer # Reutilizar serializer de Producto

class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = '__all__'

class StockSerializer(serializers.ModelSerializer):
    # Opcional: Mostrar detalles del producto y sucursal
    producto = ProductoSerializer(read_only=True)
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)
    # Campos para escribir (solo IDs)
    producto_id = serializers.IntegerField(write_only=True)
    sucursal_id = serializers.IntegerField(write_only=True)


    class Meta:
        model = Stock
        fields = ('id', 'producto', 'sucursal_nombre', 'cantidad', 'producto_id', 'sucursal_id', 'sucursal') # Incluir sucursal para escritura si es necesario
        read_only_fields = ('id', 'producto', 'sucursal_nombre', 'sucursal') # 'sucursal' como objeto es read_only