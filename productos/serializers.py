# productos/serializers.py
from rest_framework import serializers
from .models import Categoria, Marca, Producto

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__' # Incluir todos los campos

class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = '__all__'

class ProductoSerializer(serializers.ModelSerializer):
    # Opcional: Mostrar nombres en lugar de IDs para claves foráneas
    categoria_nombre = serializers.CharField(source='categoria.nombre', read_only=True)
    marca_nombre = serializers.CharField(source='marca.nombre', read_only=True)

    class Meta:
        model = Producto
        fields = ('id', 'nombre', 'precio', 'descripcion', 'capacidad', 'color',
                  'categoria', 'marca', 'categoria_nombre', 'marca_nombre', 'imagen')
        # 'categoria' y 'marca' se usan para escribir (enviar IDs)
        # 'categoria_nombre' y 'marca_nombre' son de solo lectura para mostrar nombres