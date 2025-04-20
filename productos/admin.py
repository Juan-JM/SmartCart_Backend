# productos/admin.py
from django.contrib import admin
from .models import Categoria, Marca, Producto

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'categoria', 'precio', 'color', 'capacidad', 'imagen')
    list_filter = ('marca', 'categoria', 'color')
    search_fields = ('nombre', 'descripcion', 'marca__nombre', 'categoria__nombre')
    autocomplete_fields = ['marca', 'categoria'] # Facilita la selección si hay muchos
