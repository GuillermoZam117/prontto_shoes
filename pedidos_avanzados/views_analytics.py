"""
Vistas para el sistema de analytics avanzado
Sistema POS Pronto Shoes - Enhanced Analytics Views
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .analytics import AnalyticsEngine, ReportGenerator
from .models import OrdenCliente, EstadoProductoSeguimiento
from tiendas.models import Tienda


@login_required
@permission_required('pedidos_avanzados.view_ordencliente', raise_exception=True)
def analytics_dashboard(request):
    """Dashboard principal de analytics avanzado"""
    # Parámetros de filtro
    tienda_id = request.GET.get('tienda_id')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Procesar fechas
    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    
    # Crear engine de analytics
    analytics = AnalyticsEngine(
        tienda_id=int(tienda_id) if tienda_id else None,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    
    # Obtener datos básicos para la página inicial
    metricas_generales = analytics.get_general_metrics()
    alertas = analytics.get_automated_alerts()
    
    # Context para template
    context = {
        'metricas_generales': metricas_generales,
        'alertas': alertas,
        'tiendas': Tienda.objects.filter(activa=True),
        'tienda_seleccionada': tienda_id,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d') if fecha_inicio else '',
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d') if fecha_fin else '',
        'titulo': 'Analytics Avanzado - Dashboard'
    }
    
    return render(request, 'pedidos_avanzados/analytics/dashboard.html', context)


@login_required
@cache_page(60 * 5)  # Cache por 5 minutos
def api_analytics_comprehensive(request):
    """API para obtener datos completos de analytics"""
    # Parámetros de filtro
    tienda_id = request.GET.get('tienda_id')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Crear clave de cache única
    cache_key = f"analytics_comprehensive_{tienda_id}_{fecha_inicio}_{fecha_fin}"
    
    # Verificar cache
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse(cached_data)
    
    try:
        # Procesar fechas
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        # Crear engine de analytics
        analytics = AnalyticsEngine(
            tienda_id=int(tienda_id) if tienda_id else None,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        # Obtener datos completos
        data = analytics.get_comprehensive_dashboard_data()
        
        # Guardar en cache por 5 minutos
        cache.set(cache_key, data, 300)
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error al generar analytics: {str(e)}'
        }, status=500)


@login_required
def api_analytics_metrics(request):
    """API rápida para métricas principales"""
    tienda_id = request.GET.get('tienda_id')
    
    analytics = AnalyticsEngine(
        tienda_id=int(tienda_id) if tienda_id else None
    )
    
    metrics = analytics.get_general_metrics()
    
    return JsonResponse(metrics)


@login_required
def api_analytics_temporal_trends(request):
    """API para tendencias temporales"""
    tienda_id = request.GET.get('tienda_id')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Procesar fechas
    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    
    analytics = AnalyticsEngine(
        tienda_id=int(tienda_id) if tienda_id else None,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    
    trends = analytics.get_temporal_trends()
    
    return JsonResponse(trends)


@login_required
def api_analytics_customers(request):
    """API para análisis de clientes"""
    tienda_id = request.GET.get('tienda_id')
    
    analytics = AnalyticsEngine(
        tienda_id=int(tienda_id) if tienda_id else None
    )
    
    customer_data = analytics.get_customer_analysis()
    
    return JsonResponse(customer_data)


@login_required
def api_analytics_products(request):
    """API para análisis de productos"""
    tienda_id = request.GET.get('tienda_id')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Procesar fechas
    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    
    analytics = AnalyticsEngine(
        tienda_id=int(tienda_id) if tienda_id else None,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    
    product_data = analytics.get_product_analysis()
    
    return JsonResponse(product_data)


@login_required
def analytics_reports(request):
    """Vista para generación de reportes"""
    context = {
        'tiendas': Tienda.objects.filter(activa=True),
        'titulo': 'Generador de Reportes Avanzados'
    }
    
    return render(request, 'pedidos_avanzados/analytics/reports.html', context)


@login_required
def api_generate_report(request):
    """API para generar reportes personalizados"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Parámetros del reporte
        report_type = data.get('type', 'detailed')
        tienda_id = data.get('tienda_id')
        fecha_inicio = data.get('fecha_inicio')
        fecha_fin = data.get('fecha_fin')
        formato = data.get('formato', 'json')
        
        # Procesar fechas
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        # Crear analytics engine
        analytics = AnalyticsEngine(
            tienda_id=int(tienda_id) if tienda_id else None,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        # Crear generador de reportes
        report_generator = ReportGenerator(analytics)
        
        # Generar reporte según tipo
        if report_type == 'executive':
            report_data = report_generator.generate_executive_summary()
        else:
            report_data = report_generator.generate_detailed_report()
        
        # Devolver según formato
        if formato == 'json':
            return JsonResponse(report_data)
        elif formato == 'download':
            # Para descarga JSON
            json_content = report_generator.export_to_json(report_type)
            response = HttpResponse(
                json_content,
                content_type='application/json'
            )
            filename = f'reporte_analytics_{report_type}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error al generar reporte: {str(e)}'
        }, status=500)


@login_required
def analytics_realtime_dashboard(request):
    """Dashboard en tiempo real con WebSocket"""
    context = {
        'titulo': 'Dashboard Tiempo Real',
        'websocket_enabled': True
    }
    
    return render(request, 'pedidos_avanzados/analytics/realtime_dashboard.html', context)


@login_required
def api_analytics_alerts(request):
    """API para alertas automáticas"""
    tienda_id = request.GET.get('tienda_id')
    
    analytics = AnalyticsEngine(
        tienda_id=int(tienda_id) if tienda_id else None
    )
    
    alerts = analytics.get_automated_alerts()
    
    return JsonResponse(alerts)


@login_required
def analytics_predictive(request):
    """Vista para analytics predictivo"""
    tienda_id = request.GET.get('tienda_id')
    
    analytics = AnalyticsEngine(
        tienda_id=int(tienda_id) if tienda_id else None
    )
    
    predictions = analytics.get_predictive_insights()
    
    context = {
        'predictions': predictions,
        'tiendas': Tienda.objects.filter(activa=True),
        'tienda_seleccionada': tienda_id,
        'titulo': 'Analytics Predictivo'
    }
    
    return render(request, 'pedidos_avanzados/analytics/predictive.html', context)


@login_required
def analytics_customer_segmentation(request):
    """Vista para segmentación de clientes"""
    analytics = AnalyticsEngine()
    customer_data = analytics.get_customer_analysis()
    
    context = {
        'customer_data': customer_data,
        'titulo': 'Segmentación de Clientes'
    }
    
    return render(request, 'pedidos_avanzados/analytics/customer_segmentation.html', context)


@login_required
def analytics_product_insights(request):
    """Vista para insights de productos"""
    analytics = AnalyticsEngine()
    product_data = analytics.get_product_analysis()
    
    context = {
        'product_data': product_data,
        'titulo': 'Insights de Productos'
    }
    
    return render(request, 'pedidos_avanzados/analytics/product_insights.html', context)


@login_required
def api_analytics_cache_clear(request):
    """API para limpiar cache de analytics"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    # Limpiar cache de analytics
    cache_keys = [
        key for key in cache._cache.keys() 
        if key.startswith('analytics_')
    ]
    
    for key in cache_keys:
        cache.delete(key)
    
    return JsonResponse({
        'success': True,
        'message': f'Cache limpiado: {len(cache_keys)} entradas eliminadas'
    })


@login_required
def analytics_export_dashboard(request):
    """Dashboard para exportaciones y descargas"""
    context = {
        'titulo': 'Centro de Exportaciones',
        'formatos_disponibles': [
            {'value': 'json', 'label': 'JSON'},
            {'value': 'excel', 'label': 'Excel (próximamente)'},
            {'value': 'pdf', 'label': 'PDF (próximamente)'}
        ]
    }
    
    return render(request, 'pedidos_avanzados/analytics/export_dashboard.html', context)
