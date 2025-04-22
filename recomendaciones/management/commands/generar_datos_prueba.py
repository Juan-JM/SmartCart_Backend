# recomendaciones/management/commands/generar_datos_prueba.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
import random
from decimal import Decimal

from productos.models import Producto, Categoria, Marca
from ventas.models import NotaVenta, DetalleNotaVenta
from usuarios.models import Cliente
from recomendaciones.ml import GeneradorRecomendaciones

class Command(BaseCommand):
    help = 'Genera datos de prueba para el sistema de recomendaciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ventas',
            type=int,
            default=100,
            help='Número de ventas a generar'
        )
        parser.add_argument(
            '--max-productos-por-venta',
            type=int,
            default=5,
            help='Número máximo de productos por venta'
        )

    def handle(self, *args, **options):
        num_ventas = options['ventas']
        max_productos_por_venta = options['max_productos_por_venta']
        
        self.stdout.write(self.style.NOTICE(f"Generando {num_ventas} ventas con máximo {max_productos_por_venta} productos cada una..."))
        
        # Verificar que hay productos disponibles
        productos = list(Producto.objects.all())
        if not productos:
            self.stdout.write(self.style.ERROR("No hay productos en la base de datos. Debes crear productos primero."))
            return
        
        # Verificar si hay clientes disponibles
        clientes = list(Cliente.objects.all())
        
        # Generar ventas de prueba
        self._generar_ventas(num_ventas, max_productos_por_venta, productos, clientes)
        
        # Generar recomendaciones a partir de las ventas creadas
        generador = GeneradorRecomendaciones()
        count = generador.generar_recomendaciones()
        
        if count is not None:
            self.stdout.write(
                self.style.SUCCESS(f"Se generaron {count} reglas de recomendación basadas en los datos de prueba.")
            )
        else:
            self.stdout.write(
                self.style.ERROR("Error al generar recomendaciones.")
            )
    
    def _generar_ventas(self, num_ventas, max_productos_por_venta, productos, clientes):
        """Genera ventas aleatorias para simular datos históricos."""
        try:
            # Crear una lista de combinaciones frecuentes para simular patrones
            combinaciones_frecuentes = [
                (0, 1, 2),      # Ejemplo: celular + cargador + audifonos
                (3, 4),         # Ejemplo: laptop + mouse
                (5, 6, 7),      # Otro conjunto común
                (8, 9),         # Otro conjunto común
                (10, 11, 12),   # Otro conjunto común
            ]
            
            # Asegurarse de que tenemos suficientes productos para las combinaciones
            combinaciones_validas = []
            for combo in combinaciones_frecuentes:
                if all(idx < len(productos) for idx in combo):
                    combinaciones_validas.append(combo)
            
            with transaction.atomic():
                for i in range(num_ventas):
                    # Decidir si usar una combinación frecuente (70% de probabilidad)
                    use_combo = random.random() < 0.7 and combinaciones_validas
                    
                    # Crear nota de venta
                    cliente = random.choice(clientes) if clientes and random.random() < 0.8 else None
                    nota_venta = NotaVenta.objects.create(
                        cliente=cliente,
                        fecha_hora=timezone.now() - timezone.timedelta(days=random.randint(1, 90))
                    )
                    
                    # Decidir cuántos productos incluir en esta venta
                    if use_combo:
                        # Usar una combinación frecuente
                        combo = random.choice(combinaciones_validas)
                        productos_venta = [productos[idx] for idx in combo]
                        
                        # Posiblemente agregar algunos productos aleatorios adicionales
                        if random.random() < 0.3:
                            num_adicionales = random.randint(1, max_productos_por_venta - len(combo))
                            for _ in range(num_adicionales):
                                prod_adicional = random.choice(productos)
                                if prod_adicional not in productos_venta:
                                    productos_venta.append(prod_adicional)
                    else:
                        # Seleccionar productos aleatorios
                        num_productos = random.randint(1, max_productos_por_venta)
                        productos_venta = random.sample(productos, num_productos)
                    
                    # Crear detalles de venta y calcular monto total
                    monto_total = Decimal('0.00')
                    for producto in productos_venta:
                        cantidad = random.randint(1, 3)
                        precio_unitario = producto.precio
                        subtotal = precio_unitario * cantidad
                        
                        DetalleNotaVenta.objects.create(
                            nota_venta=nota_venta,
                            producto=producto,
                            cantidad=cantidad,
                            precio_unitario=precio_unitario,
                            subtotal=subtotal
                        )
                        
                        monto_total += subtotal
                    
                    # Actualizar monto total
                    nota_venta.monto_total = monto_total
                    nota_venta.save()
                    
                    if (i + 1) % 10 == 0 or i + 1 == num_ventas:
                        self.stdout.write(f"Generadas {i + 1} de {num_ventas} ventas...")
            
            self.stdout.write(self.style.SUCCESS(f"Se generaron {num_ventas} ventas de prueba exitosamente."))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al generar ventas de prueba: {e}"))
            import traceback
            traceback.print_exc()