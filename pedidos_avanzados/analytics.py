"""
Sistema de Analytics Avanzado para Pedidos
Sistema POS Pronto Shoes - Analytics Engine
"""

from django.db.models import Q, Sum, Count, Avg, Max, Min, F, Value, Case, When
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, Coalesce
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional
import json

from .models import OrdenCliente, EstadoProductoSeguimiento, EntregaParcial, NotaCredito
from ventas.models import Pedido, DetallePedido
from clientes.models import Cliente
from productos.models import Producto
from tiendas.models import Tienda


class AnalyticsEngine:
    """Motor de analytics avanzado para el sistema de pedidos"""
    
    def __init__(self, tienda_id: Optional[int] = None, fecha_inicio: Optional[datetime] = None, fecha_fin: Optional[datetime] = None):
        self.tienda_id = tienda_id
        self.fecha_inicio = fecha_inicio or (timezone.now() - timedelta(days=30))
        self.fecha_fin = fecha_fin or timezone.now()
    
    def get_comprehensive_dashboard_data(self) -> Dict[str, Any]:
        """Genera datos completos para el dashboard de analytics"""
        return {
            'metricas_generales': self.get_general_metrics(),
            'tendencias_temporales': self.get_temporal_trends(),
            'analisis_clientes': self.get_customer_analysis(),
            'analisis_productos': self.get_product_analysis(),
            'rendimiento_ordenes': self.get_order_performance(),
            'analisis_entregas': self.get_delivery_analysis(),
            'notas_credito_insights': self.get_credit_notes_insights(),
            'predicciones': self.get_predictive_insights(),
            'alertas_automaticas': self.get_automated_alerts()
        }
    
    def get_general_metrics(self) -> Dict[str, Any]:
        """Métricas generales del sistema"""
        base_queryset = self._get_base_queryset()
        
        # Órdenes base
        ordenes = OrdenCliente.objects.filter(
            fecha_creacion__range=[self.fecha_inicio, self.fecha_fin]
        )
        if self.tienda_id:
            # Filtrar por tienda a través de pedidos relacionados
            ordenes = ordenes.filter(
                cliente__pedidos__tienda_id=self.tienda_id
            ).distinct()
        
        # Pedidos relacionados
        pedidos = base_queryset
        
        # Métricas principales
        total_ordenes = ordenes.count()
        total_pedidos = pedidos.count()
        total_ingresos = pedidos.aggregate(
            total=Coalesce(Sum('total'), Value(0))
        )['total']
        
        # Análisis de estados
        ordenes_por_estado = ordenes.values('estado').annotate(
            count=Count('id'),
            monto_total=Sum('monto_total')
        )
        
        # Tiempo promedio de cumplimiento
        ordenes_completadas = ordenes.filter(estado__in=['VENTA', 'COMPLETADO'])
        tiempo_promedio = ordenes_completadas.aggregate(
            promedio=Avg(
                F('fecha_cierre') - F('fecha_creacion')
            )
        )['promedio']
        
        # Tasa de conversión
        tasa_conversion = (
            ordenes.filter(estado='VENTA').count() / max(total_ordenes, 1) * 100
        )
        
        # Ticket promedio
        ticket_promedio = pedidos.aggregate(
            promedio=Avg('total')
        )['promedio'] or Decimal('0')
        
        return {
            'total_ordenes': total_ordenes,
            'total_pedidos': total_pedidos,
            'total_ingresos': float(total_ingresos),
            'ordenes_por_estado': list(ordenes_por_estado),
            'tiempo_promedio_cumplimiento': tiempo_promedio.total_seconds() / 3600 if tiempo_promedio else 0,
            'tasa_conversion': round(tasa_conversion, 2),
            'ticket_promedio': float(ticket_promedio),
            'ordenes_activas': ordenes.filter(estado='ACTIVO').count(),
            'ordenes_pendientes': ordenes.filter(estado='PENDIENTE').count(),
        }
    
    def get_temporal_trends(self) -> Dict[str, Any]:
        """Análisis de tendencias temporales"""
        base_queryset = self._get_base_queryset()
        
        # Tendencias diarias últimos 30 días
        tendencias_diarias = base_queryset.filter(
            fecha__gte=timezone.now() - timedelta(days=30)
        ).extra(
            select={'fecha_truncada': 'DATE(fecha)'}
        ).values('fecha_truncada').annotate(
            total_pedidos=Count('id'),
            total_ingresos=Sum('total'),
            ticket_promedio=Avg('total')
        ).order_by('fecha_truncada')
        
        # Tendencias semanales últimos 3 meses
        tendencias_semanales = base_queryset.filter(
            fecha__gte=timezone.now() - timedelta(days=90)
        ).annotate(
            semana=TruncWeek('fecha')
        ).values('semana').annotate(
            total_pedidos=Count('id'),
            total_ingresos=Sum('total')
        ).order_by('semana')
        
        # Tendencias mensuales último año
        tendencias_mensuales = base_queryset.filter(
            fecha__gte=timezone.now() - timedelta(days=365)
        ).annotate(
            mes=TruncMonth('fecha')
        ).values('mes').annotate(
            total_pedidos=Count('id'),
            total_ingresos=Sum('total')
        ).order_by('mes')
        
        # Análisis por días de la semana
        analisis_dias_semana = base_queryset.extra(
            select={'dia_semana': 'DAYOFWEEK(fecha)'}
        ).values('dia_semana').annotate(
            total_pedidos=Count('id'),
            promedio_ingresos=Avg('total')
        ).order_by('dia_semana')
        
        # Horas pico
        analisis_horas = base_queryset.extra(
            select={'hora': 'HOUR(fecha)'}
        ).values('hora').annotate(
            total_pedidos=Count('id')
        ).order_by('hora')
        
        return {
            'tendencias_diarias': list(tendencias_diarias),
            'tendencias_semanales': list(tendencias_semanales),
            'tendencias_mensuales': list(tendencias_mensuales),
            'analisis_dias_semana': list(analisis_dias_semana),
            'analisis_horas_pico': list(analisis_horas),
        }
    
    def get_customer_analysis(self) -> Dict[str, Any]:
        """Análisis detallado de clientes"""
        base_queryset = self._get_base_queryset()
        
        # Top clientes por ingresos
        top_clientes_ingresos = base_queryset.values(
            'cliente__id', 'cliente__nombre', 'cliente__email'
        ).annotate(
            total_ingresos=Sum('total'),
            total_pedidos=Count('id'),
            ultima_compra=Max('fecha'),
            ticket_promedio=Avg('total')
        ).order_by('-total_ingresos')[:20]
        
        # Top clientes por frecuencia
        top_clientes_frecuencia = base_queryset.values(
            'cliente__id', 'cliente__nombre'
        ).annotate(
            total_pedidos=Count('id'),
            total_ingresos=Sum('total')
        ).order_by('-total_pedidos')[:20]
        
        # Análisis de segmentación RFM (Recency, Frequency, Monetary)
        clientes_rfm = self._calculate_rfm_analysis()
        
        # Clientes en riesgo (sin actividad reciente)
        clientes_en_riesgo = Cliente.objects.filter(
            pedidos__fecha__lt=timezone.now() - timedelta(days=60)
        ).annotate(
            dias_sin_actividad=timezone.now().date() - Max('pedidos__fecha'),
            total_historico=Sum('pedidos__total')
        ).order_by('-total_historico')[:15]
        
        # Nuevos clientes
        nuevos_clientes = Cliente.objects.filter(
            fecha_registro__gte=self.fecha_inicio
        ).annotate(
            primer_pedido=Min('pedidos__fecha'),
            total_gastado=Sum('pedidos__total')
        ).order_by('-fecha_registro')[:10]
        
        return {
            'top_clientes_ingresos': list(top_clientes_ingresos),
            'top_clientes_frecuencia': list(top_clientes_frecuencia),
            'segmentacion_rfm': clientes_rfm,
            'clientes_en_riesgo': list(clientes_en_riesgo.values()),
            'nuevos_clientes': list(nuevos_clientes.values()),
            'resumen_clientes': {
                'total_clientes_activos': base_queryset.values('cliente').distinct().count(),
                'nuevos_este_periodo': nuevos_clientes.count(),
                'clientes_recurrentes': base_queryset.values('cliente').annotate(
                    num_pedidos=Count('id')
                ).filter(num_pedidos__gt=1).count()
            }
        }
    
    def get_product_analysis(self) -> Dict[str, Any]:
        """Análisis detallado de productos"""
        # Productos más vendidos
        productos_top = DetallePedido.objects.filter(
            pedido__fecha__range=[self.fecha_inicio, self.fecha_fin]
        )
        if self.tienda_id:
            productos_top = productos_top.filter(pedido__tienda_id=self.tienda_id)
        
        productos_mas_vendidos = productos_top.values(
            'producto__id', 'producto__codigo', 'producto__nombre'
        ).annotate(
            total_vendido=Sum('cantidad'),
            total_ingresos=Sum(F('cantidad') * F('precio_unitario')),
            num_pedidos=Count('pedido', distinct=True)
        ).order_by('-total_vendido')[:20]
        
        # Productos con mayor margen
        productos_mayor_margen = productos_top.annotate(
            margen=F('precio_unitario') - F('producto__precio_costo')
        ).values(
            'producto__id', 'producto__codigo', 'producto__nombre'
        ).annotate(
            margen_total=Sum(F('cantidad') * (F('precio_unitario') - F('producto__precio_costo'))),
            margen_promedio=Avg(F('precio_unitario') - F('producto__precio_costo'))
        ).order_by('-margen_total')[:20]
        
        # Productos con baja rotación
        productos_baja_rotacion = Producto.objects.annotate(
            vendidos_periodo=Coalesce(
                Sum(
                    'detalles__cantidad',
                    filter=Q(detalles__pedido__fecha__range=[self.fecha_inicio, self.fecha_fin])
                ),
                Value(0)
            )
        ).filter(vendidos_periodo=0).values(
            'id', 'codigo', 'nombre', 'stock_actual'
        )[:15]
        
        # Análisis de categorías
        analisis_categorias = productos_top.values(
            'producto__categoria__nombre'
        ).annotate(
            total_vendido=Sum('cantidad'),
            total_ingresos=Sum(F('cantidad') * F('precio_unitario')),
            productos_distintos=Count('producto', distinct=True)
        ).order_by('-total_ingresos')
        
        return {
            'productos_mas_vendidos': list(productos_mas_vendidos),
            'productos_mayor_margen': list(productos_mayor_margen),
            'productos_baja_rotacion': list(productos_baja_rotacion),
            'analisis_categorias': list(analisis_categorias),
            'metricas_productos': {
                'total_productos_vendidos': productos_top.aggregate(
                    total=Sum('cantidad')
                )['total'] or 0,
                'productos_distintos_vendidos': productos_top.values('producto').distinct().count(),
                'precio_promedio_venta': productos_top.aggregate(
                    promedio=Avg('precio_unitario')
                )['promedio'] or 0
            }
        }
    
    def get_order_performance(self) -> Dict[str, Any]:
        """Análisis de rendimiento de órdenes"""
        ordenes = OrdenCliente.objects.filter(
            fecha_creacion__range=[self.fecha_inicio, self.fecha_fin]
        )
        
        # Órdenes completadas para análisis de tiempo
        ordenes_completadas = ordenes.filter(
            estado__in=['VENTA', 'COMPLETADO'],
            fecha_cierre__isnull=False
        ).annotate(
            tiempo_completado=F('fecha_cierre') - F('fecha_creacion')
        )
        
        # Análisis de tiempos de cumplimiento
        tiempos_cumplimiento = ordenes_completadas.aggregate(
            tiempo_min=Min('tiempo_completado'),
            tiempo_max=Max('tiempo_completado'),
            tiempo_promedio=Avg('tiempo_completado'),
            tiempo_mediano=Avg('tiempo_completado')  # Aproximación
        )
        
        # Distribución de tiempos
        distribucion_tiempos = []
        rangos = [1, 3, 7, 14, 30]  # días
        for i, rango in enumerate(rangos):
            anterior = rangos[i-1] if i > 0 else 0
            count = ordenes_completadas.filter(
                tiempo_completado__gte=timedelta(days=anterior),
                tiempo_completado__lt=timedelta(days=rango)
            ).count()
            distribucion_tiempos.append({
                'rango': f"{anterior}-{rango} días",
                'count': count
            })
        
        # Órdenes con entregas parciales
        ordenes_con_parciales = ordenes.filter(
            cliente__in=EntregaParcial.objects.values('pedido_original__cliente')
        ).count()
        
        # Análisis de productos por orden
        productos_por_orden = ordenes.aggregate(
            promedio=Avg('total_productos'),
            maximo=Max('total_productos'),
            minimo=Min('total_productos')
        )
        
        return {
            'tiempos_cumplimiento': {
                'promedio_horas': tiempos_cumplimiento['tiempo_promedio'].total_seconds() / 3600 if tiempos_cumplimiento['tiempo_promedio'] else 0,
                'minimo_horas': tiempos_cumplimiento['tiempo_min'].total_seconds() / 3600 if tiempos_cumplimiento['tiempo_min'] else 0,
                'maximo_horas': tiempos_cumplimiento['tiempo_max'].total_seconds() / 3600 if tiempos_cumplimiento['tiempo_max'] else 0,
            },
            'distribucion_tiempos': distribucion_tiempos,
            'ordenes_con_entregas_parciales': ordenes_con_parciales,
            'productos_por_orden': productos_por_orden,
            'eficiencia_cumplimiento': {
                'completadas_a_tiempo': ordenes_completadas.filter(
                    tiempo_completado__lte=timedelta(days=7)
                ).count(),
                'total_completadas': ordenes_completadas.count()
            }
        }
    
    def get_delivery_analysis(self) -> Dict[str, Any]:
        """Análisis de entregas parciales"""
        entregas = EntregaParcial.objects.filter(
            fecha_entrega__range=[self.fecha_inicio, self.fecha_fin]
        )
        
        # Estadísticas generales
        stats_entregas = entregas.aggregate(
            total_entregas=Count('id'),
            monto_total_parcial=Sum('monto_entregado'),
            promedio_por_entrega=Avg('monto_entregado')
        )
        
        # Entregas por día
        entregas_por_dia = entregas.annotate(
            fecha_truncada=TruncDate('fecha_entrega')
        ).values('fecha_truncada').annotate(
            count=Count('id'),
            monto_total=Sum('monto_entregado')
        ).order_by('fecha_truncada')
        
        # Análisis por método de pago
        por_metodo_pago = entregas.values('metodo_pago').annotate(
            count=Count('id'),
            monto_total=Sum('monto_entregado')
        )
        
        # Tickets con más entregas parciales
        tickets_mas_parciales = entregas.values(
            'pedido_original__numero_ticket'
        ).annotate(
            num_entregas=Count('id'),
            monto_total_entregado=Sum('monto_entregado')
        ).order_by('-num_entregas')[:10]
        
        return {
            'estadisticas_generales': stats_entregas,
            'entregas_por_dia': list(entregas_por_dia),
            'por_metodo_pago': list(por_metodo_pago),
            'tickets_mas_parciales': list(tickets_mas_parciales),
            'porcentaje_ordenes_con_parciales': (
                entregas.values('pedido_original').distinct().count() /
                max(Pedido.objects.filter(fecha__range=[self.fecha_inicio, self.fecha_fin]).count(), 1) * 100
            )
        }
    
    def get_credit_notes_insights(self) -> Dict[str, Any]:
        """Análisis de notas de crédito"""
        notas = NotaCredito.objects.filter(
            fecha_creacion__range=[self.fecha_inicio, self.fecha_fin]
        )
        
        # Estadísticas generales
        stats_notas = notas.aggregate(
            total_notas=Count('id'),
            monto_total=Sum('monto'),
            promedio_nota=Avg('monto')
        )
        
        # Por estado
        por_estado = notas.values('estado').annotate(
            count=Count('id'),
            monto_total=Sum('monto')
        )
        
        # Por tipo
        por_tipo = notas.values('tipo').annotate(
            count=Count('id'),
            monto_total=Sum('monto')
        )
        
        # Notas próximas a vencer
        proximas_vencer = notas.filter(
            estado='ACTIVA',
            fecha_vencimiento__lte=timezone.now().date() + timedelta(days=30)
        ).count()
        
        # Top clientes con más notas de crédito
        clientes_mas_notas = notas.values(
            'cliente__nombre'
        ).annotate(
            total_notas=Count('id'),
            monto_total=Sum('monto')
        ).order_by('-monto_total')[:10]
        
        return {
            'estadisticas_generales': stats_notas,
            'por_estado': list(por_estado),
            'por_tipo': list(por_tipo),
            'proximas_vencer': proximas_vencer,
            'clientes_mas_notas': list(clientes_mas_notas)
        }
    
    def get_predictive_insights(self) -> Dict[str, Any]:
        """Insights predictivos simples"""
        # Proyección basada en tendencia de últimos 30 días
        ultimos_30_dias = self._get_base_queryset().filter(
            fecha__gte=timezone.now() - timedelta(days=30)
        )
        
        ingresos_diarios = ultimos_30_dias.extra(
            select={'fecha_truncada': 'DATE(fecha)'}
        ).values('fecha_truncada').annotate(
            total=Sum('total')
        )
        
        # Promedio diario últimos 30 días
        promedio_diario = sum(item['total'] for item in ingresos_diarios) / max(len(ingresos_diarios), 1)
        
        # Proyección próximos 30 días
        proyeccion_30_dias = promedio_diario * 30
        
        # Clientes que probablemente comprarán pronto (basado en patrones históricos)
        clientes_probables = Cliente.objects.filter(
            pedidos__fecha__gte=timezone.now() - timedelta(days=60)
        ).annotate(
            dias_ultima_compra=(timezone.now().date() - Max('pedidos__fecha')),
            promedio_dias_entre_compras=Avg(
                F('pedidos__fecha') - F('pedidos__fecha')
            )
        ).filter(
            dias_ultima_compra__gte=F('promedio_dias_entre_compras')
        )[:10]
        
        return {
            'proyeccion_ingresos_30_dias': float(proyeccion_30_dias),
            'promedio_diario_actual': float(promedio_diario),
            'clientes_probables_compra': list(clientes_probables.values(
                'nombre', 'email', 'dias_ultima_compra'
            )),
            'tendencia_general': 'creciente' if promedio_diario > 0 else 'estable'
        }
    
    def get_automated_alerts(self) -> Dict[str, List[Dict]]:
        """Alertas automáticas del sistema"""
        alertas = {
            'criticas': [],
            'advertencias': [],
            'informativas': []
        }
        
        # Alertas críticas
        ordenes_muy_antiguas = OrdenCliente.objects.filter(
            estado='ACTIVO',
            fecha_creacion__lt=timezone.now() - timedelta(days=30)
        ).count()
        
        if ordenes_muy_antiguas > 0:
            alertas['criticas'].append({
                'tipo': 'ordenes_antiguas',
                'mensaje': f'{ordenes_muy_antiguas} órdenes activas con más de 30 días',
                'count': ordenes_muy_antiguas
            })
        
        # Notas de crédito vencidas
        notas_vencidas = NotaCredito.objects.filter(
            estado='ACTIVA',
            fecha_vencimiento__lt=timezone.now().date()
        ).count()
        
        if notas_vencidas > 0:
            alertas['criticas'].append({
                'tipo': 'notas_vencidas',
                'mensaje': f'{notas_vencidas} notas de crédito vencidas',
                'count': notas_vencidas
            })
        
        # Alertas de advertencia
        ordenes_pendientes_mucho_tiempo = OrdenCliente.objects.filter(
            estado='PENDIENTE',
            fecha_creacion__lt=timezone.now() - timedelta(days=14)
        ).count()
        
        if ordenes_pendientes_mucho_tiempo > 0:
            alertas['advertencias'].append({
                'tipo': 'ordenes_pendientes',
                'mensaje': f'{ordenes_pendientes_mucho_tiempo} órdenes pendientes por más de 14 días',
                'count': ordenes_pendientes_mucho_tiempo
            })
        
        # Productos sin movimiento
        productos_sin_movimiento = Producto.objects.annotate(
            ventas_recientes=Count(
                'detalles',
                filter=Q(detalles__pedido__fecha__gte=timezone.now() - timedelta(days=60))
            )
        ).filter(ventas_recientes=0).count()
        
        if productos_sin_movimiento > 10:
            alertas['advertencias'].append({
                'tipo': 'productos_sin_movimiento',
                'mensaje': f'{productos_sin_movimiento} productos sin ventas en 60 días',
                'count': productos_sin_movimiento
            })
        
        return alertas
    
    def _get_base_queryset(self):
        """Queryset base para pedidos filtrado por tienda y fechas"""
        queryset = Pedido.objects.filter(
            fecha__range=[self.fecha_inicio, self.fecha_fin]
        )
        if self.tienda_id:
            queryset = queryset.filter(tienda_id=self.tienda_id)
        return queryset
    
    def _calculate_rfm_analysis(self) -> Dict[str, Any]:
        """Cálculo simple de análisis RFM"""
        # Esta es una implementación simplificada
        # En producción se podría usar algoritmos más sofisticados
        
        clientes_data = Cliente.objects.annotate(
            ultima_compra=Max('pedidos__fecha'),
            frecuencia=Count('pedidos'),
            monto_total=Sum('pedidos__total')
        ).filter(
            ultima_compra__isnull=False
        )
        
        # Segmentación simple
        clientes_premium = clientes_data.filter(
            monto_total__gte=10000,
            frecuencia__gte=5
        ).count()
        
        clientes_regulares = clientes_data.filter(
            monto_total__gte=2000,
            monto_total__lt=10000,
            frecuencia__gte=3
        ).count()
        
        clientes_nuevos = clientes_data.filter(
            monto_total__lt=2000,
            frecuencia__lt=3
        ).count()
        
        return {
            'premium': clientes_premium,
            'regulares': clientes_regulares,
            'nuevos': clientes_nuevos,
            'total_analizados': clientes_data.count()
        }


class ReportGenerator:
    """Generador de reportes en diferentes formatos"""
    
    def __init__(self, analytics_engine: AnalyticsEngine):
        self.analytics = analytics_engine
    
    def generate_executive_summary(self) -> Dict[str, Any]:
        """Genera resumen ejecutivo para gerencia"""
        data = self.analytics.get_comprehensive_dashboard_data()
        
        return {
            'periodo': {
                'inicio': self.analytics.fecha_inicio.strftime('%d/%m/%Y'),
                'fin': self.analytics.fecha_fin.strftime('%d/%m/%Y')
            },
            'kpis_principales': {
                'total_ingresos': data['metricas_generales']['total_ingresos'],
                'total_ordenes': data['metricas_generales']['total_ordenes'],
                'ticket_promedio': data['metricas_generales']['ticket_promedio'],
                'tasa_conversion': data['metricas_generales']['tasa_conversion'],
                'tiempo_promedio_cumplimiento': data['rendimiento_ordenes']['tiempos_cumplimiento']['promedio_horas']
            },
            'alertas_ejecutivas': data['alertas_automaticas']['criticas'],
            'top_clientes': data['analisis_clientes']['top_clientes_ingresos'][:5],
            'top_productos': data['analisis_productos']['productos_mas_vendidos'][:5],
            'proyecciones': data['predicciones']
        }
    
    def generate_detailed_report(self) -> Dict[str, Any]:
        """Genera reporte detallado completo"""
        return self.analytics.get_comprehensive_dashboard_data()
    
    def export_to_json(self, report_type: str = 'detailed') -> str:
        """Exporta reporte a JSON"""
        if report_type == 'executive':
            data = self.generate_executive_summary()
        else:
            data = self.generate_detailed_report()
        
        return json.dumps(data, default=str, ensure_ascii=False, indent=2)
