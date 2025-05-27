from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class ReportePersonalizado(models.Model):
    TIPO_CHOICES = [
        ('clientes_inactivos', 'Clientes sin Movimientos'),
        ('historial_precios', 'Historial de Cambios de Precios'),
        ('inventario_diario', 'Inventario Diario y Traspasos'),
        ('descuentos_mensuales', 'Descuentos Aplicados por Mes'),
        ('cumplimiento_metas', 'Cumplimiento de Metas del Tabulador'),
        ('ventas_por_vendedor', 'Ventas por Vendedor'),
        ('productos_mas_vendidos', 'Productos Más Vendidos'),
        ('analisis_rentabilidad', 'Análisis de Rentabilidad'),
        ('stock_critico', 'Stock Crítico y Alertas'),
        ('tendencias_ventas', 'Tendencias de Ventas'),
    ]
    
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True)
    parametros = models.JSONField(default=dict, blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultima_ejecucion = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Reporte Personalizado'
        verbose_name_plural = 'Reportes Personalizados'
    
    def __str__(self):
        return self.nombre

class EjecucionReporte(models.Model):
    reporte = models.ForeignKey(ReportePersonalizado, on_delete=models.CASCADE, related_name='ejecuciones')
    ejecutado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_ejecucion = models.DateTimeField(auto_now_add=True)
    parametros_utilizados = models.JSONField(default=dict)
    tiempo_ejecucion = models.FloatField(null=True, blank=True)  # en segundos
    registros_encontrados = models.IntegerField(default=0)
    archivo_generado = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-fecha_ejecucion']
        verbose_name = 'Ejecución de Reporte'
        verbose_name_plural = 'Ejecuciones de Reporte'
    
    def __str__(self):
        return f"{self.reporte.nombre} - {self.fecha_ejecucion.strftime('%d/%m/%Y %H:%M')}"
