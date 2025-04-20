# ventas/serializers.py
from rest_framework import serializers
from django.db import transaction # <--- ¡Importar transaction!
from .models import NotaVenta, DetalleNotaVenta
from productos.serializers import ProductoSerializer
from usuarios.serializers import ClienteSerializer # Para mostrar info del cliente

class DetalleNotaVentaSerializer(serializers.ModelSerializer):
        # Mostrar detalles del producto en el detalle de venta
        producto = ProductoSerializer(read_only=True)
        # Campo para escribir el ID del producto al crear/actualizar
        producto_id = serializers.IntegerField(write_only=True)

        class Meta:
            model = DetalleNotaVenta
            fields = ('id', 'producto', 'producto_id', 'cantidad', 'precio_unitario', 'subtotal')
            read_only_fields = ('subtotal', 'precio_unitario') # Se calculan o se toman del producto

class NotaVentaSerializer(serializers.ModelSerializer):
        # Mostrar detalles de la venta anidados
        detalles = DetalleNotaVentaSerializer(many=True, read_only=True)
        # Mostrar info básica del cliente
        cliente = ClienteSerializer(read_only=True)
        # Campo para asignar cliente por ID al crear
        cliente_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

        # Campo para recibir los detalles al crear una nota de venta completa
        detalles_payload = serializers.ListField(
            child=serializers.DictField(), write_only=True, required=True
        )
        # Ejemplo de dict en detalles_payload: {'producto_id': 1, 'cantidad': 2}

        class Meta:
            model = NotaVenta
            fields = ('id', 'cliente', 'cliente_id', 'monto_total', 'fecha_hora', 'detalles', 'detalles_payload')
            read_only_fields = ('monto_total', 'fecha_hora', 'detalles') # Se calculan o se definen automáticamente

        @transaction.atomic
        def create(self, validated_data):
            # Extraer el payload de detalles y el ID del cliente
            detalles_data = validated_data.pop('detalles_payload')
            cliente_id = validated_data.pop('cliente_id', None)

            # Crear la NotaVenta principal
            nota_venta = NotaVenta.objects.create(cliente_id=cliente_id, **validated_data)
            monto_total_calculado = 0

            # Crear los DetallesNotaVenta asociados
            from productos.models import Producto # Importar aquí para evitar dependencia circular
            for item_data in detalles_data:
                producto_id = item_data['producto_id']
                cantidad = item_data['cantidad']
                try:
                    # Obtener el producto y su precio actual
                    producto = Producto.objects.get(id=producto_id)
                    precio_unitario = producto.precio
                    subtotal = cantidad * precio_unitario

                    DetalleNotaVenta.objects.create(
                        nota_venta=nota_venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                        # subtotal se calcula en el save del modelo DetalleNotaVenta
                    )
                    monto_total_calculado += subtotal

                    # --- ¡IMPORTANTE! Aquí deberías descontar el stock ---
                    # Necesitas saber de qué sucursal descontar. Esto complica el flujo
                    # y quizás la creación de la venta debería ser más compleja o
                    # manejarse en un endpoint específico que reciba la sucursal.
                    # Ejemplo simple (requiere lógica adicional):
                    # stock_item = Stock.objects.get(producto=producto, sucursal_id=ID_DE_SUCURSAL)
                    # stock_item.cantidad -= cantidad
                    # stock_item.save()

                except Producto.DoesNotExist:
                    # Manejar error si el producto no existe
                    raise serializers.ValidationError(f"Producto con ID {producto_id} no encontrado.")
                except Exception as e: # Capturar otras posibles excepciones (ej. Stock no encontrado)
                    # Es crucial revertir la transacción si algo falla
                    raise serializers.ValidationError(f"Error procesando item {producto_id}: {str(e)}")


            # Actualizar el monto total de la NotaVenta
            nota_venta.monto_total = monto_total_calculado
            nota_venta.save()

            return nota_venta
        

