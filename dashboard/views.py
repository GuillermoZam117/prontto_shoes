from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import json
from django.db.models import Sum

# This is a simplified version of the dashboard view that will be enhanced 
# as we implement more functionality in the application.
@login_required
def index(request):
    today = timezone.now().date()
    context = {
        'ventas_hoy': '0.00',  # Will be populated when ventas module is implemented
        'ventas_mes': '0.00',  # Will be populated when ventas module is implemented
        'pedidos_pendientes': 0,  # Will be populated when pedidos module is implemented
        'stock_bajo': 0,  # Will be populated when inventario module is implemented
        'actividades': [],  # Will be populated when logging module is implemented
        'pedidos': [],  # Will be populated when pedidos module is implemented
        'productos_populares': [],  # Will be populated when productos module is implemented
        # Sample data for chart
        'fechas': json.dumps([d.strftime('%d-%m-%Y') for d in [today - timedelta(days=i) for i in range(6, -1, -1)]]),
        'ventas_diarias': json.dumps([0, 0, 0, 0, 0, 0, 0]),  # Sample data for now
    }
    return render(request, 'dashboard/index.html', context)

@login_required
def sidebar_demo(request):
    """
    Demo page to showcase the new sidebar functionality
    """
    context = {
        'page_title': 'Sidebar Demo',
        'mobile_title': 'Sidebar Demo',
    }
    return render(request, 'sidebar_demo.html', context)

# API endpoint to get dashboard data for real-time updates
@login_required
def dashboard_data(request):
    from django.http import JsonResponse
    
    data = {
        'ventas_hoy': '0.00',  # Will be populated when ventas module is implemented
        'ventas_mes': '0.00',  # Will be populated when ventas module is implemented
        'pedidos_pendientes': 0,  # Will be populated when pedidos module is implemented
        'stock_bajo': 0,  # Will be populated when inventario module is implemented
        'nuevos_pedidos': 0,  # Will be populated when pedidos module is implemented
    }
    
    return JsonResponse(data)
