from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from .models import Cliente, Anticipo, DescuentoCliente
from .serializers import ClienteSerializer, AnticipoSerializer, DescuentoClienteSerializer
from django_filters.rest_framework import DjangoFilterBackend
# Mejora Swagger:
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from ventas.models import Pedido
from caja.models import TransaccionCaja, Caja
from django.db import transaction
from datetime import date
from decimal import Decimal # Import Decimal
from django.contrib.auth.decorators import login_required
from tiendas.models import Tienda
from django.db.models import Q, Sum, Avg
from django.utils import timezone
from django.contrib import messages
from rest_framework.exceptions import ValidationError
from .forms import ClienteForm, AnticipoForm, DescuentoClienteForm # Import DescuentoClienteForm
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

# Frontend views
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
            cliente.created_by = request.user
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
            cliente_actualizado = form.save(commit=False)
            cliente_actualizado.updated_by = request.user
            cliente_actualizado.save()
            messages.success(request, f"Cliente '{cliente_actualizado.nombre}' actualizado exitosamente.")
            return redirect('clientes:detalle', pk=cliente_actualizado.pk)
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = ClienteForm(instance=cliente)
    
    context = {
        'form': form,
        'cliente': cliente, # Para mostrar info adicional si es necesario
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
    anticipos = Anticipo.objects.select_related('cliente', 'created_by')
    
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
            try:
                with transaction.atomic():
                    anticipo = form.save(commit=False)
                    anticipo.created_by = request.user
                    anticipo.save()

                    cliente_obj = anticipo.cliente 
                    # Asegurarse de que saldo_a_favor no sea None antes de sumar
                    cliente_obj.saldo_a_favor = (cliente_obj.saldo_a_favor or Decimal(0)) + anticipo.monto
                    cliente_obj.save()

                    user = request.user
                    user_tienda = None

                    # Intentar obtener la tienda del usuario. Esta lógica puede necesitar ajuste
                    # dependiendo de cómo se estructuren los perfiles de usuario o modelos de empleado.
                    if hasattr(user, 'tienda') and user.tienda: # Asume que el user tiene un atributo 'tienda'
                        user_tienda = user.tienda
                    # Ejemplo de cómo podría ser con un perfil:
                    # elif hasattr(user, 'perfil_empleado') and user.perfil_empleado.tienda_actual:
                    #     user_tienda = user.perfil_empleado.tienda_actual
                    
                    if not user_tienda:
                        # Fallback: usar la tienda del cliente para la transacción de caja
                        user_tienda = cliente_obj.tienda 
                        if user_tienda:
                            messages.info(request, f"Transacción de caja se registrará en la tienda del cliente ('{user_tienda.nombre}') ya que la tienda del usuario no está definida explícitamente.")
                        else:
                            # Si ni el usuario ni el cliente tienen una tienda definida, no se puede registrar en caja.
                            messages.error(request, "Anticipo guardado, pero no se pudo determinar la tienda para la transacción de caja (ni del usuario ni del cliente).")
                    
                    if user_tienda:
                        try:
                            caja_abierta = Caja.objects.get(tienda=user_tienda, fecha=date.today(), cerrada=False)
                            TransaccionCaja.objects.create(
                                caja=caja_abierta,
                                tipo_movimiento='ingreso',
                                monto=anticipo.monto,
                                descripcion=f'Anticipo Cliente #{cliente_obj.id} - {cliente_obj.nombre}',
                                anticipo=anticipo,
                                created_by=user
                            )
                            messages.success(request, f"Anticipo de ${anticipo.monto} para {cliente_obj.nombre} y transacción de caja registrados en tienda '{user_tienda.nombre}'.")
                        except Caja.DoesNotExist:
                            messages.warning(request, f"Anticipo para {cliente_obj.nombre} guardado, pero no se encontró una caja abierta en la tienda '{user_tienda.nombre}' para registrar la transacción.")
                        except Exception as e_caja:
                            messages.error(request, f"Anticipo para {cliente_obj.nombre} guardado, pero ocurrió un error al registrar la transacción de caja: {str(e_caja)}")
                    # Si user_tienda sigue siendo None después de los fallbacks, el mensaje de error ya se habrá emitido (o el de info si se usó la del cliente).
                    
                    return redirect('clientes:anticipos')
            except Exception as e:
                messages.error(request, f"Error general al registrar el anticipo: {str(e)}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        initial_data = {}
        selected_client_id = request.GET.get('cliente')
        if selected_client_id:
            try:
                Cliente.objects.get(pk=selected_client_id) # Validate client exists
                initial_data['cliente'] = selected_client_id
            except Cliente.DoesNotExist:
                messages.warning(request, f"El cliente con ID {selected_client_id} no existe.")
        form = AnticipoForm(initial=initial_data)
    
    context = {
        'form': form,
        'titulo': 'Registrar Nuevo Anticipo'
    }
    return render(request, 'clientes/anticipo_form.html', context)

@login_required
def descuento_list(request):
    """Vista para listar descuentos"""
    # Get filter parameters
    cliente_id = request.GET.get('cliente', '')
    mes = request.GET.get('mes', '')
    
    # Base query
    descuentos = DescuentoCliente.objects.select_related('cliente')
    
    # Apply filters
    if cliente_id:
        descuentos = descuentos.filter(cliente_id=cliente_id)
    
    if mes:
        descuentos = descuentos.filter(mes_vigente__startswith=mes)
    
    # Get clients for filter dropdown
    clientes = Cliente.objects.all()
    
    # Calculate statistics for summary cards
    descuento_promedio = descuentos.aggregate(Avg('porcentaje'))['porcentaje__avg'] or 0
    clientes_unicos = descuentos.values('cliente').distinct().count()
    
    context = {
        'descuentos': descuentos,
        'clientes': clientes,
        'cliente_id': cliente_id,
        'mes': mes,
        'descuento_promedio': descuento_promedio,
        'clientes_unicos': clientes_unicos,
    }
    
    return render(request, 'clientes/descuento_list.html', context)

@login_required
def descuento_create(request):
    """Vista para crear o actualizar un descuento para un cliente y mes."""
    if request.method == 'POST':
        form = DescuentoClienteForm(request.POST)
        if form.is_valid():
            try:
                cliente = form.cleaned_data['cliente']
                mes_vigente = form.cleaned_data['mes_vigente']

                defaults = {
                    'porcentaje': form.cleaned_data['porcentaje'],
                    'monto_acumulado_mes_anterior': form.cleaned_data['monto_acumulado_mes_anterior'],
                    'updated_by': request.user
                }
                
                # Use a transaction to ensure atomicity if needed, though update_or_create is generally atomic for its operation.
                # with transaction.atomic():
                obj, created = DescuentoCliente.objects.update_or_create(
                    cliente=cliente,
                    mes_vigente=mes_vigente,
                    defaults=defaults
                )

                if created:
                    obj.created_by = request.user
                    obj.save(update_fields=['created_by']) # Save only the created_by field if it's a new object
                    messages.success(request, f"Descuento del {obj.porcentaje}% creado para {cliente.nombre} en {mes_vigente}.")
                else:
                    # obj already has updated_by from defaults and was saved by update_or_create
                    messages.success(request, f"Descuento para {cliente.nombre} en {mes_vigente} actualizado a {obj.porcentaje}%.")
                return redirect('clientes:descuentos')
            except Exception as e:
                messages.error(request, f"Error al registrar el descuento: {str(e)}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        initial_data = {}
        selected_client_id = request.GET.get('cliente')
        if selected_client_id:
            try:
                Cliente.objects.get(pk=selected_client_id)
                initial_data['cliente'] = selected_client_id
            except Cliente.DoesNotExist:
                messages.warning(request, f"El cliente con ID {selected_client_id} no existe.")
        
        current_month_year = timezone.now().strftime('%Y-%m')
        initial_data['mes_vigente'] = current_month_year # Pre-fill current month

        form = DescuentoClienteForm(initial=initial_data)
    
    context = {
        'form': form,
        'titulo': 'Registrar/Actualizar Descuento de Cliente'
    }
    return render(request, 'clientes/descuento_form.html', context)

@login_required
@require_http_methods(["DELETE"])
def cliente_delete(request, pk):
    """Vista para eliminar un cliente con validaciones"""
    try:
        cliente = get_object_or_404(Cliente, pk=pk)
        
        # Validaciones antes de eliminar
        # 1. Verificar si tiene pedidos pendientes
        pedidos_pendientes = Pedido.objects.filter(
            cliente=cliente, 
            estado__in=['PENDIENTE', 'PROCESO']
        ).count()
        
        if pedidos_pendientes > 0:
            if request.headers.get('HX-Request'):
                return render(request, 'clientes/partials/cliente_table.html', {
                    'clientes': Cliente.objects.select_related('tienda').order_by('nombre'),
                    'error_message': f'No se puede eliminar {cliente.nombre}. Tiene {pedidos_pendientes} pedido(s) pendiente(s).'
                })
            return JsonResponse({
                'success': False,
                'message': f'No se puede eliminar {cliente.nombre}. Tiene {pedidos_pendientes} pedido(s) pendiente(s).'
            }, status=400)
        
        # 2. Verificar si tiene saldo a favor
        if cliente.saldo_a_favor > 0:
            if request.headers.get('HX-Request'):
                return render(request, 'clientes/partials/cliente_table.html', {
                    'clientes': Cliente.objects.select_related('tienda').order_by('nombre'),
                    'error_message': f'No se puede eliminar {cliente.nombre}. Tiene saldo a favor de ${cliente.saldo_a_favor}.'
