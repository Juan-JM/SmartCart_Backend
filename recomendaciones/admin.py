# recomendaciones/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta

from .models import ReglaAsociacion, ConfiguracionRecomendacion
from .ml import GeneradorRecomendaciones

@admin.register(ReglaAsociacion)
class ReglaAsociacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto_origen_nombre', 'producto_recomendado_nombre', 
                    'soporte_formato', 'confianza_formato', 'lift_formato', 'ultima_actualizacion')
    list_filter = ('ultima_actualizacion',)
    search_fields = ('producto_origen__nombre', 'producto_recomendado__nombre')
    readonly_fields = ('soporte', 'confianza', 'lift', 'ultima_actualizacion')
    date_hierarchy = 'ultima_actualizacion'
    list_per_page = 20
    
    def producto_origen_nombre(self, obj):
        return obj.producto_origen.nombre
    producto_origen_nombre.short_description = 'Producto Origen'
    
    def producto_recomendado_nombre(self, obj):
        return obj.producto_recomendado.nombre
    producto_recomendado_nombre.short_description = 'Producto Recomendado'
    
    def soporte_formato(self, obj):
        return format_html('<span title="{}%">{:.4f}</span>', obj.soporte * 100, obj.soporte)
    soporte_formato.short_description = 'Soporte'
    
    def confianza_formato(self, obj):
        return format_html('<span title="{}%">{:.2f}</span>', obj.confianza * 100, obj.confianza)
    confianza_formato.short_description = 'Confianza'
    
    def lift_formato(self, obj):
        color = 'green' if obj.lift > 1.5 else ('orange' if obj.lift > 1 else 'red')
        return format_html('<span style="color: {};" title="Correlación: {}">{:.2f}</span>', 
                           color, 
                           'Fuerte' if obj.lift > 1.5 else ('Positiva' if obj.lift > 1 else 'Débil'), 
                           obj.lift)
    lift_formato.short_description = 'Lift'

@admin.register(ConfiguracionRecomendacion)
class ConfiguracionRecomendacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'soporte_minimo_formato', 'confianza_minima_formato', 
                    'lift_minimo', 'max_recomendaciones', 'frecuencia_actualizacion_dias', 
                    'ultima_actualizacion', 'acciones')
    readonly_fields = ('ultima_actualizacion',)
    
    def soporte_minimo_formato(self, obj):
        return f"{obj.soporte_minimo * 100:.2f}%"
    soporte_minimo_formato.short_description = 'Soporte Mínimo'
    
    def confianza_minima_formato(self, obj):
        return f"{obj.confianza_minima * 100:.2f}%"
    confianza_minima_formato.short_description = 'Confianza Mínima'
    
    def acciones(self, obj):
        return format_html(
            '<a class="button" href="{}">Generar Recomendaciones</a>',
            f'/admin/recomendaciones/configuracionrecomendacion/{obj.id}/generar/'
        )
    acciones.short_description = 'Acciones'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/generar/',
                self.admin_site.admin_view(self.generar_recomendaciones_view),
                name='configuracionrecomendacion-generar'),
            path('dashboard/',
                self.admin_site.admin_view(self.dashboard_view),
                name='recomendaciones-dashboard'),
        ]
        return custom_urls + urls
    
    def generar_recomendaciones_view(self, request, object_id, *args, **kwargs):
        config = self.get_object(request, object_id)
        
        if request.method == 'POST':
            try:
                generador = GeneradorRecomendaciones()
                count = generador.generar_recomendaciones()
                
                if count is not None:
                    self.message_user(request, f"Se generaron {count} reglas de recomendación exitosamente.")
                else:
                    self.message_user(request, "Error al generar recomendaciones.", level='ERROR')
            except Exception as e:
                self.message_user(request, f"Error: {str(e)}", level='ERROR')
            
            return self.response_post_save_change(request, config)
        
        context = self.admin_site.each_context(request)
        context.update({
            'title': 'Generar Recomendaciones',
            'object': config,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        })
        
        return TemplateResponse(request, 'admin/recomendaciones/generar_recomendaciones.html', context)
    
    def dashboard_view(self, request, *args, **kwargs):
        # Obtener estadísticas generales
        total_reglas = ReglaAsociacion.objects.count()
        
        # Promedios de métricas
        promedios = ReglaAsociacion.objects.aggregate(
            avg_soporte=Avg('soporte'),
            avg_confianza=Avg('confianza'),
            avg_lift=Avg('lift')
        )
        
        # Productos más recomendados
        from django.db.models import Count
        productos_mas_recomendados = ReglaAsociacion.objects.values(
            'producto_recomendado__id', 'producto_recomendado__nombre'
        ).annotate(
            total=Count('producto_recomendado')
        ).order_by('-total')[:10]
        
        # Productos que generan más recomendaciones
        productos_origen = ReglaAsociacion.objects.values(
            'producto_origen__id', 'producto_origen__nombre'
        ).annotate(
            total=Count('producto_origen')
        ).order_by('-total')[:10]
        
        # Efectividad de recomendaciones (esto requeriría un modelo para seguimiento de clicks)
        # En este ejemplo, usaremos datos simulados
        efectividad = {
            'clicks_totales': 1250,
            'conversiones': 320,
            'tasa_conversion': 25.6,
            'promedio_ingreso': 4500.50,
        }
        
        # Tendencia de uso de recomendaciones (simulado)
        tendencia = [
            {'fecha': '2023-04-15', 'clicks': 45, 'conversiones': 12},
            {'fecha': '2023-04-16', 'clicks': 52, 'conversiones': 14},
            {'fecha': '2023-04-17', 'clicks': 48, 'conversiones': 10},
            {'fecha': '2023-04-18', 'clicks': 60, 'conversiones': 15},
            {'fecha': '2023-04-19', 'clicks': 75, 'conversiones': 22},
            {'fecha': '2023-04-20', 'clicks': 85, 'conversiones': 21},
            {'fecha': '2023-04-21', 'clicks': 92, 'conversiones': 24},
        ]
        
        context = self.admin_site.each_context(request)
        context.update({
            'title': 'Dashboard de Recomendaciones',
            'total_reglas': total_reglas,
            'promedios': promedios,
            'productos_mas_recomendados': productos_mas_recomendados,
            'productos_origen': productos_origen,
            'efectividad': efectividad,
            'tendencia': tendencia,
            'opts': self.model._meta,
            'app_label': self.model._meta.app_label,
        })
        
        return TemplateResponse(request, 'admin/recomendaciones/dashboard.html', context)