# recomendaciones/ml.py
import pandas as pd
import numpy as np
from mlxtend.frequent_patterns import apriori, association_rules
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Q

from ventas.models import NotaVenta, DetalleNotaVenta
from productos.models import Producto
from .models import ReglaAsociacion, ConfiguracionRecomendacion

class GeneradorRecomendaciones:
    """
    Clase para generar reglas de asociación utilizando el algoritmo Apriori
    basado en el historial de ventas.
    """
    
    def __init__(self):
        # Obtener configuración o usar valores predeterminados
        try:
            self.config = ConfiguracionRecomendacion.objects.first()
            if not self.config:
                self.config = ConfiguracionRecomendacion.objects.create()
        except Exception as e:
            print(f"Error al obtener configuración: {e}")
            self.config = ConfiguracionRecomendacion()
        
        self.min_support = self.config.soporte_minimo
        self.min_confidence = self.config.confianza_minima
        self.min_lift = self.config.lift_minimo
    
    def _obtener_datos_transacciones(self):
        """
        Recopila los datos de transacciones desde el modelo NotaVenta.
        
        Returns:
            DataFrame con las transacciones (cada fila es una nota de venta,
            y cada columna indica la presencia o ausencia de un producto).
        """
        print("Obteniendo datos de transacciones...")
        
        # Consultar todas las notas de venta con sus detalles
        detalles = DetalleNotaVenta.objects.select_related(
            'nota_venta', 'producto'
        ).all()
        
        # Crear una lista de transacciones
        # Cada transacción es un diccionario {nota_venta_id: id, producto_id: id}
        transacciones = [
            {'nota_venta_id': detalle.nota_venta_id, 'producto_id': detalle.producto_id}
            for detalle in detalles
        ]
        
        if not transacciones:
            print("No hay transacciones disponibles.")
            return None
        
        # Convertir a DataFrame
        df_transacciones = pd.DataFrame(transacciones)
        
        # Convertir a formato binario (cada fila es una nota de venta, cada columna es un producto)
        df_pivot = pd.pivot_table(
            df_transacciones, 
            index='nota_venta_id', 
            columns='producto_id', 
            aggfunc=lambda x: 1,
            fill_value=0
        )
        
        print(f"Datos de transacciones obtenidos. Shape: {df_pivot.shape}")
        return df_pivot
    
    def _aplicar_apriori(self, df_transacciones):
        """
        Aplica el algoritmo Apriori para encontrar conjuntos frecuentes.
        
        Args:
            df_transacciones: DataFrame con las transacciones en formato binario.
            
        Returns:
            DataFrame con conjuntos frecuentes y sus métricas de soporte.
        """
        print(f"Aplicando Apriori (min_support={self.min_support})...")
        
        # Aplicar Apriori para encontrar conjuntos frecuentes
        frequent_itemsets = apriori(
            df_transacciones, 
            min_support=self.min_support,
            use_colnames=True,
            max_len=2  # Solo queremos pares de productos
        )
        
        if frequent_itemsets.empty:
            print("No se encontraron conjuntos frecuentes.")
            return None
        
        print(f"Conjuntos frecuentes encontrados: {len(frequent_itemsets)}")
        return frequent_itemsets
    
    def _generar_reglas(self, frequent_itemsets):
        """
        Genera reglas de asociación a partir de conjuntos frecuentes.
        
        Args:
            frequent_itemsets: DataFrame con conjuntos frecuentes.
            
        Returns:
            DataFrame con reglas de asociación y sus métricas.
        """
        print(f"Generando reglas (min_confidence={self.min_confidence}, min_lift={self.min_lift})...")
        
        # Generar reglas de asociación
        rules = association_rules(
            frequent_itemsets, 
            metric="confidence", 
            min_threshold=self.min_confidence
        )
        
        # Filtrar por lift mínimo
        rules = rules[rules['lift'] >= self.min_lift]
        
        # Solo nos interesan las reglas donde antecedente y consecuente son un solo producto
        rules = rules[(rules['antecedents'].apply(len) == 1) & 
                      (rules['consequents'].apply(len) == 1)]
        
        if rules.empty:
            print("No se generaron reglas con los criterios especificados.")
            return None
        
        print(f"Reglas generadas: {len(rules)}")
        return rules
    
    def _guardar_reglas(self, rules):
        """
        Guarda las reglas generadas en la base de datos.
        
        Args:
            rules: DataFrame con reglas de asociación.
            
        Returns:
            Número de reglas guardadas.
        """
        print("Guardando reglas en la base de datos...")
        
        # Comenzar transacción para mantener integridad
        with transaction.atomic():
            # Eliminar reglas anteriores
            ReglaAsociacion.objects.all().delete()
            
            # Contar reglas guardadas
            count = 0
            
            # Procesar cada regla
            for _, row in rules.iterrows():
                # Extraer IDs de productos de la regla
                antecedent_id = list(row['antecedents'])[0]
                consequent_id = list(row['consequents'])[0]
                
                try:
                    # Crear nueva regla
                    ReglaAsociacion.objects.create(
                        producto_origen_id=antecedent_id,
                        producto_recomendado_id=consequent_id,
                        soporte=row['support'],
                        confianza=row['confidence'],
                        lift=row['lift']
                    )
                    count += 1
                except Exception as e:
                    print(f"Error al guardar regla ({antecedent_id} → {consequent_id}): {e}")
            
            # Actualizar la fecha de última actualización
            self.config.ultima_actualizacion = timezone.now()
            self.config.save()
            
        print(f"Reglas guardadas: {count}")
        return count
    
    def generar_recomendaciones(self):
        """
        Proceso principal para generar recomendaciones.
        
        Returns:
            Número de reglas generadas, o None si hubo un error.
        """
        try:
            # 1. Obtener datos de transacciones
            df_transacciones = self._obtener_datos_transacciones()
            if df_transacciones is None or df_transacciones.empty:
                return None
            
            # 2. Aplicar Apriori
            frequent_itemsets = self._aplicar_apriori(df_transacciones)
            if frequent_itemsets is None or frequent_itemsets.empty:
                return None
            
            # 3. Generar reglas
            rules = self._generar_reglas(frequent_itemsets)
            if rules is None or rules.empty:
                return None
            
            # 4. Guardar reglas en la base de datos
            count = self._guardar_reglas(rules)
            
            return count
        except Exception as e:
            print(f"Error al generar recomendaciones: {e}")
            import traceback
            traceback.print_exc()
            return None

