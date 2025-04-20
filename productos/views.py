# productos/views.py
from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Categoria, Marca, Producto
from .serializers import CategoriaSerializer, MarcaSerializer, ProductoSerializer
from core.permissions import IsAdminOrReadOnly # Reutiliza el permiso

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    # Cualquiera puede ver, solo Admin puede editar/crear/borrar
    permission_classes = [IsAdminOrReadOnly]

class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer
    permission_classes = [IsAdminOrReadOnly] # Mismo permiso

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related('categoria', 'marca').all() # Optimiza
    serializer_class = ProductoSerializer
    permission_classes = [IsAdminOrReadOnly]
    
    # Habilitamos los filtros y búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categoria', 'marca', 'color', 'capacidad']
    search_fields = ['nombre', 'descripcion', 'marca__nombre', 'categoria__nombre']
    ordering_fields = ['nombre', 'precio']
    ordering = ['nombre']  # Ordenamiento por defecto
    
# # productos/views.py
# from rest_framework import viewsets, permissions
# from .models import Categoria, Marca, Producto
# from .serializers import CategoriaSerializer, MarcaSerializer, ProductoSerializer
# from core.permissions import IsAdminOrReadOnly # Reutiliza el permiso

# class CategoriaViewSet(viewsets.ModelViewSet):
#     queryset = Categoria.objects.all()
#     serializer_class = CategoriaSerializer
#     # Cualquiera puede ver, solo Admin puede editar/crear/borrar
#     permission_classes = [IsAdminOrReadOnly]

# class MarcaViewSet(viewsets.ModelViewSet):
#     queryset = Marca.objects.all()
#     serializer_class = MarcaSerializer
#     permission_classes = [IsAdminOrReadOnly] # Mismo permiso

# class ProductoViewSet(viewsets.ModelViewSet):
#     queryset = Producto.objects.select_related('categoria', 'marca').all() # Optimiza
#     serializer_class = ProductoSerializer
#     # Cualquiera puede ver la lista y detalles de productos
#     # Solo personal autorizado (Admin, Reponedor?) puede crear/editar/borrar
#     # Ajusta el permiso según quién gestiona productos (¿Reponedor o solo Admin?)
#     permission_classes = [IsAdminOrReadOnly] # Cambia si Reponedor puede editar

#     # Puedes añadir filtros aquí si necesitas (ej. por categoría, marca)
#     # filter_backends = [DjangoFilterBackend, filters.SearchFilter]
#     # filterset_fields = ['categoria', 'marca']
#     # search_fields = ['nombre', 'descripcion']