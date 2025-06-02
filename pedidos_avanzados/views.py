"""
Vistas para el sistema de pedidos avanzados
Sistema POS Pronto Shoes
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Sum, Count, Prefetch
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import (
    OrdenCliente, EstadoProductoSeguimiento, EntregaParcial,
    NotaCredito, PortalClientePolitica, ProductoCompartir
)
from .services import (
    ServicioPedidosAvanzados, ServicioAutomatizacionClientes,
    ServicioCompartirProductos
)
from ventas.models import Pedido, DetallePedido
from clientes.models import Cliente
from productos.models import Producto


@login_required
def dashboard_pedidos_avanzados(request):
    """
    Dashboard principal para pedidos avanzados
    Muestra métricas y órdenes activas
    """
    # Estadísticas generales
    ordenes_activas = OrdenCliente.objects.filter(estado='ACTIVO').count()
    ordenes_pendientes = OrdenCliente.objects.filter(estado='PENDIENTE').count()
    total_productos_pendientes = OrdenCliente.objects.filter(
        estado__in=['ACTIVO', 'PENDIENTE']
    ).aggregate(Sum('total_productos'))['total_productos__sum'] or 0
    
    # Órdenes recientes con prefetch para optimizar consultas
    ordenes_recientes = OrdenCliente.objects.select_related(
        'cliente'
    ).prefetch_related(
        'cliente__ordenes_cliente'
    ).filter(
        estado__in=['ACTIVO', 'PENDIENTE']
    ).order_by('-fecha_creacion')[:10]
    
    # Notas de crédito próximas a vencer (próximos 7 días)
    fecha_limite = timezone.now().date() + timedelta(days=7)
    notas_por_vencer = NotaCredito.objects.filter(
        estado='ACTIVA',
        fecha_vencimiento__lte=fecha_limite
    ).select_related('cliente').order_by('fecha_vencimiento')[:5]
    
    context = {
        'ordenes_activas': ordenes_activas,
        'ordenes_pendientes': ordenes_pendientes,
        'total_productos_pendientes': total_productos_pendientes,
        'ordenes_recientes': ordenes_recientes,
        'notas_por_vencer': notas_por_vencer,
        'titulo': 'Dashboard Pedidos Avanzados',
    }
    
    return render(request, 'pedidos_avanzados/dashboard.html', context)


@login_required
def grilla_ordenes_multiple(request):
    """
    Interfaz de grilla para manejo de múltiples órdenes
    Permite gestión simultánea de múltiples órdenes por cliente
    """
    # Filtros de búsqueda
    search_query = request.GET.get('search', '')
    estado_filter = request.GET.get('estado', '')
    cliente_filter = request.GET.get('cliente', '')
    
    # Query base con optimizaciones
    ordenes = OrdenCliente.objects.select_related(
        'cliente', 'created_by'
    ).prefetch_related(
        Prefetch(
            'cliente__pedidos',
            queryset=Pedido.objects.filter(estado='PENDIENTE')
        )
    )
    
    # Aplicar filtros
    if search_query:
        ordenes = ordenes.filter(
            Q(numero_orden__icontains=search_query) |
            Q(cliente__nombre__icontains=search_query) |
            Q(cliente__telefono__icontains=search_query)
        )
    
    if estado_filter:
        ordenes = ordenes.filter(estado=estado_filter)
    
    if cliente_filter:
        ordenes = ordenes.filter(cliente_id=cliente_filter)
    
    # Ordenar por fecha de creación descendente
    ordenes = ordenes.order_by('-fecha_creacion')
    
    # Lista de clientes para filtro
    clientes_con_ordenes = Cliente.objects.filter(
        ordenes_cliente__isnull=False
    ).distinct().order_by('nombre')
    
    # Estados para filtro
    estados_disponibles = OrdenCliente.ESTADO_CHOICES
    
    context = {
        'ordenes': ordenes,
        'clientes_con_ordenes': clientes_con_ordenes,
        'estados_disponibles': estados_disponibles,
        'search_query': search_query,
        'estado_filter': estado_filter,
        'cliente_filter': cliente_filter,
        'titulo': 'Gestión Múltiple de Órdenes',
    }
    
    return render(request, 'pedidos_avanzados/grilla_ordenes_multiple.html', context)


@login_required
def detalle_orden_cliente(request, orden_id):
    """
    Vista detallada de una orden de cliente
    Muestra todos los pedidos asociados y su seguimiento
    """
    orden = get_object_or_404(
        OrdenCliente.objects.select_related('cliente'),
        id=orden_id
    )
    
    # Pedidos asociados a esta orden (simulación - en producción esto vendría de una relación)
    pedidos_asociados = Pedido.objects.filter(
        cliente=orden.cliente,
        fecha_pedido__gte=orden.fecha_creacion,
        estado='PENDIENTE'
    ).prefetch_related(
        'detalle_pedidos__producto',
        'detalle_pedidos__seguimientos'
    )
    
    # Seguimientos de productos
    seguimientos = EstadoProductoSeguimiento.objects.filter(
        detalle_pedido__pedido__in=pedidos_asociados
    ).select_related(
        'detalle_pedido__producto', 'usuario_cambio', 'proveedor'
    ).order_by('-fecha_cambio')[:20]
    
    # Entregas parciales
    entregas_parciales = EntregaParcial.objects.filter(
        pedido_original__in=pedidos_asociados
    ).select_related('usuario_entrega').order_by('-fecha_entrega')
    
    # Notas de crédito del cliente
    notas_credito = NotaCredito.objects.filter(
        cliente=orden.cliente
    ).order_by('-created_at')[:5]
    
    context = {
        'orden': orden,
        'pedidos_asociados': pedidos_asociados,
        'seguimientos': seguimientos,
        'entregas_parciales': entregas_parciales,
        'notas_credito': notas_credito,
        'titulo': f'Orden {orden.numero_orden}',
    }
    
    return render(request, 'pedidos_avanzados/detalle_orden.html', context)


@login_required
def crear_orden_desde_pedidos(request):
    """
    Vista para crear una nueva orden consolidando pedidos existentes
    """
    if request.method == 'POST':
        try:
            cliente_id = request.POST.get('cliente_id')
            pedidos_ids = request.POST.getlist('pedidos_ids')
            observaciones = request.POST.get('observaciones', '')
            
            cliente = get_object_or_404(Cliente, id=cliente_id)
            pedidos = Pedido.objects.filter(id__in=pedidos_ids, cliente=cliente)
            
            # Usar el servicio para crear la orden
            servicio = ServicioPedidosAvanzados()
            orden = servicio.crear_orden_desde_pedidos(
                cliente=cliente,
                pedidos=list(pedidos),
                observaciones=observaciones,
                usuario=request.user
            )
            
            messages.success(
                request, 
                f'Orden {orden.numero_orden} creada exitosamente con {len(pedidos)} pedidos.'
            )
            
            return redirect('pedidos_avanzados:detalle_orden', orden_id=orden.id)
            
        except Exception as e:
            messages.error(request, f'Error al crear orden: {str(e)}')
            return redirect('pedidos_avanzados:grilla_ordenes_multiple')
    
    # GET - Mostrar formulario
    cliente_id = request.GET.get('cliente_id')
    cliente = None
    pedidos_disponibles = []
    
    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        pedidos_disponibles = Pedido.objects.filter(
            cliente=cliente,
            estado='PENDIENTE'
        ).prefetch_related('detalle_pedidos__producto')
    
    # Lista de clientes con pedidos pendientes
    clientes_con_pedidos = Cliente.objects.filter(
        pedidos__estado='PENDIENTE'
    ).distinct().order_by('nombre')
    
    context = {
        'cliente': cliente,
        'pedidos_disponibles': pedidos_disponibles,
        'clientes_con_pedidos': clientes_con_pedidos,
        'titulo': 'Crear Orden desde Pedidos',
    }
    
    return render(request, 'pedidos_avanzados/crear_orden.html', context)


@login_required
def portal_cliente_view(request, cliente_id=None):
    """
    Portal del cliente para ver sus órdenes y notas de crédito
    """
    cliente = None
    ordenes = []
    notas_credito = []
    productos_compartidos = []
    
    if cliente_id:
        cliente = get_object_or_404(Cliente, id=cliente_id)
        
        # Órdenes del cliente
        ordenes = OrdenCliente.objects.filter(
            cliente=cliente
        ).order_by('-fecha_creacion')
        
        # Notas de crédito activas
        notas_credito = NotaCredito.objects.filter(
            cliente=cliente,
            estado='ACTIVA'
        ).order_by('-created_at')
        
        # Productos compartidos recientemente
        productos_compartidos = ProductoCompartir.objects.filter(
            cliente=cliente
        ).select_related('producto').order_by('-fecha_compartido')[:10]
    
    # Políticas y FAQs para el portal
    politicas = PortalClientePolitica.objects.filter(
        activo=True,
        tipo='POLITICA'
    ).order_by('orden_display')
    
    faqs = PortalClientePolitica.objects.filter(
        activo=True,
        tipo='FAQ'
    ).order_by('orden_display')
    
    # Lista de clientes para selector
    clientes_activos = Cliente.objects.filter(
        activo=True
    ).order_by('nombre')
    
    context = {
        'cliente': cliente,
        'ordenes': ordenes,
        'notas_credito': notas_credito,
        'productos_compartidos': productos_compartidos,
        'politicas': politicas,
        'faqs': faqs,
        'clientes_activos': clientes_activos,
        'titulo': f'Portal Cliente - {cliente.nombre}' if cliente else 'Portal Cliente',
    }
    
    return render(request, 'pedidos_avanzados/portal_cliente.html', context)


@login_required
def gestionar_entregas_parciales(request):
    """
    Vista para gestionar entregas parciales
    """
    # Filtros
    search_query = request.GET.get('search', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    entregas = EntregaParcial.objects.select_related(
        'pedido_original__cliente',
        'pedido_nuevo__cliente',
        'usuario_entrega'
    )
    
    # Aplicar filtros
    if search_query:
        entregas = entregas.filter(
            Q(ticket_entrega__icontains=search_query) |
            Q(pedido_original__cliente__nombre__icontains=search_query)
        )
    
    if fecha_desde:
        entregas = entregas.filter(fecha_entrega__gte=fecha_desde)
    
    if fecha_hasta:
        entregas = entregas.filter(fecha_entrega__lte=fecha_hasta)
    
    entregas = entregas.order_by('-fecha_entrega')
    
    context = {
        'entregas': entregas,
        'search_query': search_query,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'titulo': 'Gestión de Entregas Parciales',
    }
    
    return render(request, 'pedidos_avanzados/entregas_parciales.html', context)


@login_required
def reportes_avanzados(request):
    """
    Reportes avanzados del sistema de pedidos
    """
    # Métricas de órdenes por estado
    ordenes_por_estado = {}
    for estado_code, estado_name in OrdenCliente.ESTADO_CHOICES:
        ordenes_por_estado[estado_name] = OrdenCliente.objects.filter(
            estado=estado_code
        ).count()
    
    # Top clientes por número de órdenes
    top_clientes = Cliente.objects.annotate(
        num_ordenes=Count('ordenes_cliente')
    ).filter(num_ordenes__gt=0).order_by('-num_ordenes')[:10]
    
    # Productos más compartidos
    productos_mas_compartidos = Producto.objects.annotate(
        num_compartidos=Count('compartidos')
    ).filter(num_compartidos__gt=0).order_by('-num_compartidos')[:10]
    
    # Notas de crédito por vencer (próximos 30 días)
    fecha_limite = timezone.now().date() + timedelta(days=30)
    notas_por_vencer = NotaCredito.objects.filter(
        estado='ACTIVA',
        fecha_vencimiento__lte=fecha_limite
    ).select_related('cliente').order_by('fecha_vencimiento')
    
    # Resumen de entregas parciales del mes actual
    inicio_mes = timezone.now().replace(day=1)
    entregas_mes = EntregaParcial.objects.filter(
        fecha_entrega__gte=inicio_mes
    ).aggregate(
        total_entregas=Count('id'),
        monto_total=Sum('monto_entregado')
    )
    
    context = {
        'ordenes_por_estado': ordenes_por_estado,
        'top_clientes': top_clientes,
        'productos_mas_compartidos': productos_mas_compartidos,
        'notas_por_vencer': notas_por_vencer,
        'entregas_mes': entregas_mes,
        'titulo': 'Reportes Avanzados',
    }
    
    return render(request, 'pedidos_avanzados/reportes.html', context)


# Vistas AJAX para funcionalidades dinámicas

@login_required
def ajax_actualizar_estado_orden(request):
    """
    Actualiza el estado de una orden vía AJAX
    """
    if request.method == 'POST':
        try:
            orden_id = request.POST.get('orden_id')
            nuevo_estado = request.POST.get('estado')
            
            orden = get_object_or_404(OrdenCliente, id=orden_id)
            orden.estado = nuevo_estado
            orden.updated_by = request.user
            
            if nuevo_estado in ['VENTA', 'CANCELADO']:
                orden.fecha_cierre = timezone.now()
            
            orden.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Estado actualizado a {orden.get_estado_display()}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
def ajax_obtener_pedidos_cliente(request):
    """
    Obtiene los pedidos pendientes de un cliente vía AJAX
    """
    cliente_id = request.GET.get('cliente_id')
    
    if not cliente_id:
        return JsonResponse({'success': False, 'message': 'Cliente no especificado'})
    
    try:
        pedidos = Pedido.objects.filter(
            cliente_id=cliente_id,
            estado='PENDIENTE'
        ).prefetch_related('detalle_pedidos__producto').values(
            'id',
            'fecha_pedido',
            'total',
            'detalle_pedidos__producto__codigo',
            'detalle_pedidos__cantidad'
        )
        
        # Formatear datos para el frontend
        pedidos_data = []
        for pedido in pedidos:
            pedidos_data.append({
                'id': pedido['id'],
                'fecha_pedido': pedido['fecha_pedido'].strftime('%d/%m/%Y'),
                'total': float(pedido['total']),
                'productos': f"{pedido['detalle_pedidos__cantidad']}x {pedido['detalle_pedidos__producto__codigo']}"
            })
        
        return JsonResponse({
            'success': True,
            'pedidos': pedidos_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })
