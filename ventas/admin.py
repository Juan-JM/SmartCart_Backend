# # ventas/admin.py
# from django.contrib import admin
# # QUITA Cliente de esta importación
# from .models import NotaVenta, DetalleNotaVenta
# # from usuarios.models import Cliente # <--- Elimina esta línea o coméntala

# class DetalleNotaVentaInline(admin.TabularInline):
#     model = DetalleNotaVenta
#     fields = ('producto', 'cantidad', 'precio_unitario', 'subtotal')
#     readonly_fields = ('subtotal',)
#     extra = 0
#     # Asegúrate de que ProductoAdmin (en productos/admin.py) tenga search_fields
#     autocomplete_fields = ['producto']

# @admin.register(NotaVenta)
# class NotaVentaAdmin(admin.ModelAdmin):
#     # Añadir 'sucursal' a list_display y list_filter si lo añadiste al modelo
#     list_display = ('id', 'cliente', 'sucursal', 'monto_total', 'fecha_hora')
#     list_filter = ('fecha_hora', 'cliente', 'sucursal') # Añadir sucursal
#     # Ajustar search_fields si es necesario
#     search_fields = ('id', 'cliente__nombre', 'cliente__usuario__username', 'sucursal__nombre')
#     readonly_fields = ('monto_total', 'fecha_hora')
#     inlines = [DetalleNotaVentaInline]
#     # Esto ahora buscará ClienteAdmin en usuarios/admin.py
#     # Añadir 'sucursal' si también quieres autocompletarla
#     autocomplete_fields = ['cliente', 'sucursal']

# ventas/admin.py
from django.contrib import admin
from .models import NotaVenta, DetalleNotaVenta

class DetalleNotaVentaInline(admin.TabularInline): # Usar TabularInline para detalles
    model = DetalleNotaVenta
    fields = ('producto', 'cantidad', 'precio_unitario', 'subtotal')
    readonly_fields = ('subtotal',) # El subtotal se calcula
    extra = 0 # No mostrar formularios extra por defecto
    autocomplete_fields = ['producto']

@admin.register(NotaVenta)
class NotaVentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'monto_total', 'fecha_hora')
    list_filter = ('fecha_hora', 'cliente')
    search_fields = ('id', 'cliente__nombre', 'cliente__usuario__username')
    readonly_fields = ('monto_total', 'fecha_hora') # Se calculan o se ponen automáticamente
    inlines = [DetalleNotaVentaInline] # Añadir los detalles inline
    autocomplete_fields = ['cliente']