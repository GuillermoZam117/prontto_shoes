from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Avg
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from decimal import Decimal
from datetime import date

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.utils.dateparse import parse_date

from .models import Cliente, Anticipo, DescuentoCliente
from .serializers import ClienteSerializer, AnticipoSerializer, DescuentoClienteSerializer
from .forms import ClienteForm, AnticipoForm, DescuentoClienteForm
from tiendas.models import Tienda
from ventas.models import Pedido
from caja.models import TransaccionCaja, Caja

# =============================================================================
# FRONTEND VIEWS
# =============================================================================

@login_required
def cliente_list(request):
    """Vista para listar clientes con soporte para HTMX"""
    # Get filter parameters
    search_query = request.GET.get('q', '')
    tienda_id = request.GET.get('tienda', '')
    
    # Base query
    clientes = Cliente.objects.select_related('tienda')
    
    # Apply filters
    if search_query:
        clientes = clientes.filter(
            Q(nombre__icontains=search_query) | 
            Q(contacto__icontains=search_query)
        )
    
    if tienda_id:
        clientes = clientes.filter(tienda_id=tienda_id)
    
    # Order results
    clientes = clientes.order_by('nombre')
    
    # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        # Return only the table partial for HTMX requests
        context = {
            'clientes': clientes,
            'search_query': search_query,
            'tienda_seleccionada': tienda_id,
        }
        return render(request, 'clientes/partials/cliente_table.html', context)
    
    # Full page render for regular requests
    # Get tiendas for filter dropdown
    tiendas = Tienda.objects.all()
    
    # Calculate metrics for summary cards
    clientes_con_saldo = Cliente.objects.filter(saldo_a_favor__gt=0).count()
    clientes_con_descuento = Cliente.objects.filter(monto_acumulado__gt=0).count()
    
    # Count advances in the current month
    anticipos_mes = Anticipo.objects.filter(
        fecha__year=timezone.now().year,
        fecha__month=timezone.now().month
    ).count()
    
    context = {
        'clientes': clientes,
        'tiendas': tiendas,
        'search_query': search_query,
        'tienda_seleccionada': tienda_id,
        'clientes_con_saldo': clientes_con_saldo,
        'clientes_con_descuento': clientes_con_descuento,
        'anticipos_mes': anticipos_mes,
    }
    
    return render(request, 'clientes/cliente_list.html', context)

@login_required
def cliente_detail(request, pk):
    """Vista de detalle de un cliente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    # Get recent orders
    pedidos = Pedido.objects.filter(cliente=cliente).order_by('-fecha')[:10]
    
    # Get anticipos
    anticipos = Anticipo.objects.filter(cliente=cliente).order_by('-fecha')
    
    # Get discount history
    descuentos = DescuentoCliente.objects.filter(cliente=cliente).order_by('-mes_vigente')
    
    # Current month's discount
    current_month = timezone.now().strftime('%Y-%m')
    descuento_actual = descuentos.filter(mes_vigente=current_month).first()
    
    context = {
        'cliente': cliente,
        'pedidos': pedidos,
        'anticipos': anticipos,
        'descuentos': descuentos,
        'descuento_actual': descuento_actual,
    }
    
    return render(request, 'clientes/cliente_detail.html', context)

@login_required
def cliente_create(request):
    """Vista para crear un nuevo cliente"""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            # Asignar tienda del usuario si existe
            if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'tienda'):
                cliente.tienda = request.user.profile.tienda
            cliente.save()
            messages.success(request, f"Cliente '{cliente.nombre}' creado exitosamente.")
            return redirect('clientes:detalle', pk=cliente.pk)
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = ClienteForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nuevo Cliente'
    }
    return render(request, 'clientes/cliente_form.html', context)

@login_required
def cliente_edit(request, pk):
    """Vista para editar un cliente existente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente_actualizado = form.save()
            messages.success(request, f"Cliente '{cliente_actualizado.nombre}' actualizado exitosamente.")
            return redirect('clientes:detalle', pk=cliente_actualizado.pk)
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = ClienteForm(instance=cliente)
    
    context = {
        'form': form,
        'cliente': cliente,
        'titulo': f'Editar Cliente: {cliente.nombre}'
    }
    return render(request, 'clientes/cliente_form.html', context)

@login_required
def anticipo_list(request):
    """Vista para listar anticipos"""
    # Get filter parameters
    cliente_id = request.GET.get('cliente', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    # Base query
    anticipos = Anticipo.objects.select_related('cliente')
    
    # Apply filters
    if cliente_id:
        anticipos = anticipos.filter(cliente_id=cliente_id)
    
    if fecha_desde:
        anticipos = anticipos.filter(fecha__gte=parse_date(fecha_desde))
    
    if fecha_hasta:
        anticipos = anticipos.filter(fecha__lte=parse_date(fecha_hasta))
    
    # Get clients for filter dropdown
    clientes = Cliente.objects.all()
    
    # Calculate metrics for summary cards
    monto_total = anticipos.aggregate(Sum('monto'))['monto__sum'] or 0
    anticipo_promedio = anticipos.aggregate(Avg('monto'))['monto__avg'] or 0
    
    context = {
        'anticipos': anticipos,
        'clientes': clientes,
        'cliente_id': cliente_id,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'monto_total': monto_total,
        'anticipo_promedio': anticipo_promedio,
    }
    
    return render(request, 'clientes/anticipo_list.html', context)

@login_required
def anticipo_create(request):
    """Vista para crear un nuevo anticipo"""
    if request.method == 'POST':
        form = AnticipoForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                anticipo = form.save(commit=False)
                anticipo.save()
                
                # Update client's balance
                cliente = anticipo.cliente
                cliente.saldo_a_favor += anticipo.monto
                cliente.save()
                
                messages.success(request, f"Anticipo de ${anticipo.monto} creado para {cliente.nombre}.")
                return redirect('clientes:anticipos')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = AnticipoForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nuevo Anticipo'
    }
    return render(request, 'clientes/anticipo_form.html', context)

@login_required
def descuento_list(request):
    """Vista para listar descuentos de clientes"""
    # Get filter parameters
    cliente_id = request.GET.get('cliente', '')
    mes_vigente = request.GET.get('mes', '')
    
    # Base query
    descuentos = DescuentoCliente.objects.select_related('cliente')
    
    # Apply filters
    if cliente_id:
        descuentos = descuentos.filter(cliente_id=cliente_id)
    
    if mes_vigente:
        descuentos = descuentos.filter(mes_vigente=mes_vigente)
    
    # Get clients for filter dropdown
    clientes = Cliente.objects.all()
    
    context = {
        'descuentos': descuentos,
        'clientes': clientes,
        'cliente_id': cliente_id,
        'mes_vigente': mes_vigente,
    }
    
    return render(request, 'clientes/descuento_list.html', context)

@login_required
def descuento_create(request):
    """Vista para crear un nuevo descuento"""
    if request.method == 'POST':
        form = DescuentoClienteForm(request.POST)
        if form.is_valid():
            descuento = form.save()
            messages.success(request, f"Descuento creado para {descuento.cliente.nombre}.")
            return redirect('clientes:descuentos')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = DescuentoClienteForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nuevo Descuento'
    }
    return render(request, 'clientes/descuento_form.html', context)

@login_required
@require_http_methods(["POST", "DELETE"])
def cliente_delete(request, pk):
    """Vista para eliminar un cliente con validaciones"""
    cliente = get_object_or_404(Cliente, pk=pk)
    
    try:
        # Check if client has pending orders
        pedidos_pendientes = Pedido.objects.filter(
            cliente=cliente, 
            estado__in=['pendiente', 'en_proceso']
        ).count()
        
        if pedidos_pendientes > 0:
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': False,
                    'message': f'No se puede eliminar el cliente {cliente.nombre}. Tiene {pedidos_pendientes} pedido(s) pendiente(s).'
                }, status=400)
            else:
                messages.error(request, f'No se puede eliminar el cliente {cliente.nombre}. Tiene {pedidos_pendientes} pedido(s) pendiente(s).')
                return redirect('clientes:lista')
        
        # Check if client has balance in favor
        if cliente.saldo_a_favor > 0:
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': False,
                    'message': f'No se puede eliminar el cliente {cliente.nombre}. Tiene un saldo a favor de ${cliente.saldo_a_favor}.'
                }, status=400)
            else:
                messages.error(request, f'No se puede eliminar el cliente {cliente.nombre}. Tiene un saldo a favor de ${cliente.saldo_a_favor}.')
                return redirect('clientes:lista')
          # Check if client has any advances (always allow deletion for now)
        # anticipos = Anticipo.objects.filter(cliente=cliente).count()
        # Note: In the future, you might want to add business logic here
        
        # If all validations pass, delete the client
        nombre_cliente = cliente.nombre
        cliente.delete()
        
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'message': f'Cliente {nombre_cliente} eliminado exitosamente.'
            })
        else:
            messages.success(request, f'Cliente {nombre_cliente} eliminado exitosamente.')
            return redirect('clientes:lista')
            
    except Exception as e:
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar el cliente: {str(e)}'
            }, status=500)
        else:
            messages.error(request, f'Error al eliminar el cliente: {str(e)}')
            return redirect('clientes:lista')

# =============================================================================
# API VIEWSETS (DRF)
# =============================================================================

class ClienteViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de clientes vía API"""
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tienda']
    search_fields = ['nombre', 'contacto']
    ordering_fields = ['nombre', 'created_at', 'saldo_a_favor']
    ordering = ['nombre']

    @extend_schema(
        summary="Obtener historial de compras de un cliente",
        responses={200: "Lista de pedidos del cliente"}
    )
    @action(detail=True, methods=['get'])
    def historial_compras(self, request, pk=None):
        """Obtener historial de compras de un cliente"""
        cliente = self.get_object()
        pedidos = Pedido.objects.filter(cliente=cliente).order_by('-fecha')[:20]
        
        historial = []
        for pedido in pedidos:
            historial.append({
                'id': pedido.id,
                'fecha': pedido.fecha,
                'total': pedido.total,
                'estado': pedido.estado,
                'productos_count': pedido.detalles.count()
            })
        
        return Response({
            'cliente': self.get_serializer(cliente).data,
            'historial': historial
        })

class AnticipoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de anticipos vía API"""
    queryset = Anticipo.objects.all()
    serializer_class = AnticipoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente']
    ordering = ['-fecha']

class DescuentoClienteViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de descuentos de clientes vía API"""
    queryset = DescuentoCliente.objects.all()
    serializer_class = DescuentoClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'mes_vigente']
    ordering = ['-mes_vigente']
