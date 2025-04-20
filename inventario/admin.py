# inventario/admin.py
from django.contrib import admin
from .models import Sucursal, Stock

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion')
    search_fields = ('nombre',)

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('producto', 'sucursal', 'cantidad')
    list_filter = ('sucursal',)
    search_fields = ('producto__nombre', 'sucursal__nombre')
    autocomplete_fields = ['producto', 'sucursal']