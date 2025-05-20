from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from .models import Cliente, Anticipo, DescuentoCliente
from .serializers import ClienteSerializer, AnticipoSerializer, DescuentoClienteSerializer
from django_filters.rest_framework import DjangoFilterBackend
# Mejora Swagger:
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, OpenApiExample
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from ventas.models import Pedido
from caja.models import TransaccionCaja, Caja
from django.db import transaction
from datetime import date
from django.contrib.auth.decorators import login_required
from tiendas.models import Tienda
from django.db.models import Q, Sum, Avg
from django.utils import timezone
from django.contrib import messages
from rest_framework.exceptions import ValidationError

# Frontend views
@login_required
def cliente_list(request):
    """Vista para listar clientes"""
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
    
    # Get tiendas for filter dropdown
    tiendas = Tienda.objects.all()
    
    # Calculate metrics for summary cards
    # Count clients with positive balance
    clientes_con_saldo = Cliente.objects.filter(saldo_a_favor__gt=0).count()
    
    # Count advances in the current month
    current_month = timezone.now().strftime('%Y-%m')
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
    tiendas = Tienda.objects.all()
    
    if request.method == 'POST':
        try:
            # Get form data
            nombre = request.POST.get('nombre', '').strip()
            contacto = request.POST.get('contacto', '').strip()
            tienda_id = request.POST.get('tienda')
            saldo_a_favor = request.POST.get('saldo_a_favor', 0)
            puntos_lealtad = request.POST.get('puntos_lealtad', 0)
            max_return_days = request.POST.get('max_return_days', 15)
            observaciones = request.POST.get('observaciones', '').strip()
            
            # Validate required fields
            if not nombre:
                messages.error(request, "El nombre del cliente es obligatorio.")
                return redirect('clientes:nuevo')
            
            if not tienda_id:
                messages.error(request, "Debe seleccionar una tienda.")
                return redirect('clientes:nuevo')
            
            # Create cliente
            cliente = Cliente.objects.create(
                nombre=nombre,
                contacto=contacto,
                tienda_id=tienda_id,
                saldo_a_favor=saldo_a_favor,
                puntos_lealtad=puntos_lealtad,
                max_return_days=max_return_days,
                observaciones=observaciones,
                created_by=request.user
            )
            
            messages.success(request, f"Cliente '{nombre}' creado exitosamente.")
            return redirect('clientes:detalle', pk=cliente.pk)
        
        except Exception as e:
            messages.error(request, f"Error al crear el cliente: {str(e)}")
    
    context = {
        'tiendas': tiendas,
    }
    
    return render(request, 'clientes/cliente_form.html', context)

@login_required
def cliente_edit(request, pk):
    """Vista para editar un cliente existente"""
    cliente = get_object_or_404(Cliente, pk=pk)
    tiendas = Tienda.objects.all()
    
    if request.method == 'POST':
        try:
            # Get form data
            nombre = request.POST.get('nombre', '').strip()
            contacto = request.POST.get('contacto', '').strip()
            tienda_id = request.POST.get('tienda')
            saldo_a_favor = request.POST.get('saldo_a_favor', 0)
            puntos_lealtad = request.POST.get('puntos_lealtad', 0)
            max_return_days = request.POST.get('max_return_days', 15)
            observaciones = request.POST.get('observaciones', '').strip()
            
            # Validate required fields
            if not nombre:
                messages.error(request, "El nombre del cliente es obligatorio.")
                return redirect('clientes:editar', pk=cliente.pk)
            
            if not tienda_id:
                messages.error(request, "Debe seleccionar una tienda.")
                return redirect('clientes:editar', pk=cliente.pk)
            
            # Update cliente
            cliente.nombre = nombre
            cliente.contacto = contacto
            cliente.tienda_id = tienda_id
            cliente.saldo_a_favor = saldo_a_favor
            cliente.puntos_lealtad = puntos_lealtad
            cliente.max_return_days = max_return_days
            cliente.observaciones = observaciones
            cliente.save()
            
            messages.success(request, f"Cliente '{nombre}' actualizado exitosamente.")
            return redirect('clientes:detalle', pk=cliente.pk)
        
        except Exception as e:
            messages.error(request, f"Error al actualizar el cliente: {str(e)}")
    
    context = {
        'cliente': cliente,
        'tiendas': tiendas,
        'is_edit': True,
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
    clientes = Cliente.objects.all()
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                cliente_id = request.POST.get('cliente')
                monto = request.POST.get('monto', 0)
                fecha = request.POST.get('fecha', date.today().isoformat())
                observaciones = request.POST.get('observaciones', '').strip()
                
                # Validate data
                if not cliente_id or not monto:
                    messages.error(request, "Cliente y monto son obligatorios.")
                    return redirect('clientes:nuevo_anticipo')
                
                # Convert to proper types
                monto = float(monto)
                fecha_obj = parse_date(fecha) if fecha else date.today()
                
                # Get client
                cliente = get_object_or_404(Cliente, pk=cliente_id)
                
                # Create advance
                anticipo = Anticipo.objects.create(
                    cliente=cliente,
                    monto=monto,
                    fecha=fecha_obj,
                    observaciones=observaciones,
                    created_by=request.user
                )
                
                # Update client balance
                cliente.saldo_a_favor += monto
                cliente.save()
                
                # Register cash transaction
                user = request.user
                if not hasattr(user, 'tienda') or user.tienda is None:
                    raise ValidationError("Usuario no asociado a una tienda.")
                
                try:
                    # Find the open cash register for the user's store and today's date
                    caja_abierta = Caja.objects.get(tienda=user.tienda, fecha=date.today(), cerrada=False)
                except Caja.DoesNotExist:
                    raise ValidationError("No hay una caja abierta para registrar el anticipo.")
                
                # Create cash transaction
                TransaccionCaja.objects.create(
                    caja=caja_abierta,
                    tipo_movimiento='ingreso',
                    monto=monto,
                    descripcion=f'Anticipo Cliente #{cliente.id} - {cliente.nombre}',
                    anticipo=anticipo,
                    created_by=user
                )
                
                messages.success(request, f"Anticipo de ${monto} registrado correctamente.")
                return redirect('clientes:anticipos')
                
        except Exception as e:
            messages.error(request, f"Error al registrar el anticipo: {str(e)}")
    
    # Pre-select client from query parameter
    selected_client = request.GET.get('cliente', '')
    
    context = {
        'clientes': clientes,
        'selected_client': selected_client,
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
    """Vista para crear un nuevo descuento"""
    clientes = Cliente.objects.all()
    
    if request.method == 'POST':
        try:
            # Get form data
            cliente_id = request.POST.get('cliente')
            mes_vigente = request.POST.get('mes_vigente')
            porcentaje = request.POST.get('porcentaje', 0)
            monto_acumulado_mes_anterior = request.POST.get('monto_acumulado_mes_anterior', 0)
            observaciones = request.POST.get('observaciones', '').strip()
            
            # Validate data
            if not cliente_id or not mes_vigente:
                messages.error(request, "Cliente y mes vigente son obligatorios.")
                return redirect('clientes:nuevo_descuento')
            
            # Get client
            cliente = get_object_or_404(Cliente, pk=cliente_id)
            
            # Check if discount already exists for this client and month
            existing_discount = DescuentoCliente.objects.filter(
                cliente=cliente,
                mes_vigente=mes_vigente
            ).first()
            
            if existing_discount:
                messages.warning(request, f"Ya existe un descuento para el cliente {cliente.nombre} en el mes {mes_vigente}. Se actualizará el existente.")
                # Update existing discount
                existing_discount.porcentaje = porcentaje
                existing_discount.monto_acumulado_mes_anterior = monto_acumulado_mes_anterior
                existing_discount.observaciones = observaciones
                existing_discount.save()
            else:
                # Create new discount
                DescuentoCliente.objects.create(
                    cliente=cliente,
                    mes_vigente=mes_vigente,
                    porcentaje=porcentaje,
                    monto_acumulado_mes_anterior=monto_acumulado_mes_anterior,
                    observaciones=observaciones,
                    created_by=request.user
                )
            
            messages.success(request, f"Descuento del {porcentaje}% registrado correctamente para {cliente.nombre}.")
            return redirect('clientes:descuentos')
            
        except Exception as e:
            messages.error(request, f"Error al registrar el descuento: {str(e)}")
    
    # Pre-select client from query parameter
    selected_client = request.GET.get('cliente', '')
    
    context = {
        'clientes': clientes,
        'selected_client': selected_client,
    }
    
    return render(request, 'clientes/descuento_form.html', context)

# API viewsets
@extend_schema(tags=["Clientes"])
class ClienteViewSet(viewsets.ModelViewSet):
    """
    Gestiona el alta, consulta, edición y filtrado de clientes.
    """
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['nombre', 'contacto', 'saldo_a_favor', 'tienda']

    @extend_schema(
        description="Crea un nuevo cliente.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'nombre': {'type': 'string', 'description': 'Nombre del cliente', 'example': 'Zapatería El Paso'},
                    'contacto': {'type': 'string', 'description': 'Contacto', 'example': 'Juan Pérez'},
                    'observaciones': {'type': 'string', 'description': 'Observaciones', 'example': 'Cliente frecuente'},
                    'saldo_a_favor': {'type': 'number', 'description': 'Saldo a favor', 'example': 0},
                    'tienda': {'type': 'integer', 'description': 'ID de tienda', 'example': 1},
                },
                'required': ['nombre', 'tienda']
            }
        },
        responses={201: ClienteSerializer}
    )
    def create(self, request, *args, **kwargs):
        """Crea un cliente nuevo y lo retorna."""
        return super().create(request, *args, **kwargs)

    @extend_schema(
        description="Reporte: Clientes sin movimientos (compras) en un periodo determinado. Parámetros: fecha_inicio, fecha_fin (YYYY-MM-DD)",
        parameters=[
            OpenApiParameter('fecha_inicio', OpenApiTypes.DATE, description="Fecha de inicio (YYYY-MM-DD)", required=True),
            OpenApiParameter('fecha_fin', OpenApiTypes.DATE, description="Fecha de fin (YYYY-MM-DD)", required=True),
        ],
        responses={200: ClienteSerializer(many=True)}
    )
    @action(detail=False, methods=["get"], url_path="sin_movimientos")
    def clientes_sin_movimientos(self, request):
        """
        Reporte: Clientes sin movimientos (compras) en un periodo determinado.
        Parámetros: fecha_inicio, fecha_fin (YYYY-MM-DD)
        Devuelve los clientes que no han realizado pedidos en el rango de fechas indicado.
        """
        fecha_inicio = request.query_params.get("fecha_inicio")
        fecha_fin = request.query_params.get("fecha_fin")
        if not fecha_inicio or not fecha_fin:
            return Response({"error": "Debe proporcionar fecha_inicio y fecha_fin en formato YYYY-MM-DD."}, status=400)
        try:
            fecha_inicio = parse_date(fecha_inicio)
            fecha_fin = parse_date(fecha_fin)
        except Exception:
            return Response({"error": "Formato de fecha inválido."}, status=400)
        if not fecha_inicio or not fecha_fin:
            return Response({"error": "Formato de fecha inválido."}, status=400)
        # IDs de clientes con pedidos en el rango
        clientes_con_pedidos = Pedido.objects.filter(
            fecha__date__gte=fecha_inicio,
            fecha__date__lte=fecha_fin
        ).values_list("cliente_id", flat=True).distinct()
        # Clientes sin pedidos en el rango
        clientes_sin = Cliente.objects.exclude(id__in=clientes_con_pedidos)
        page = self.paginate_queryset(clientes_sin)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(clientes_sin, many=True)
        return Response(serializer.data)

@extend_schema(tags=["Anticipos"])
class AnticipoViewSet(viewsets.ModelViewSet):
    """
    Gestiona anticipos de clientes.
    """
    queryset = Anticipo.objects.all()
    serializer_class = AnticipoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'fecha']

    def perform_create(self, serializer):
        # Save the anticipation
        anticipo = serializer.save(created_by=self.request.user)

        # Record the transaction in the cash register
        today = date.today()
        user = self.request.user

        if not hasattr(user, 'tienda') or user.tienda is None:
             # This case should ideally be handled by permissions or earlier validation
             raise ValidationError("User is not associated with a store.")

        try:
            # Find the open cash box for the user's store and today's date
            caja_abierta = Caja.objects.get(tienda=user.tienda, fecha=today, cerrada=False)
        except Caja.DoesNotExist:
             raise ValidationError("No hay una caja abierta para su tienda en la fecha actual para registrar el anticipo.")

        # Create TransaccionCaja entry for the income
        TransaccionCaja.objects.create(
            caja=caja_abierta,
            tipo_movimiento='ingreso',
            monto=anticipo.monto,
            descripcion=f'Anticipo Cliente #{anticipo.cliente.id}',
            anticipo=anticipo, # Link to the anticipation record
            created_by=user
        )

@extend_schema(tags=["DescuentosClientes"])
class DescuentoClienteViewSet(viewsets.ModelViewSet):
    """
    Gestiona descuentos aplicados a clientes.
    """
    queryset = DescuentoCliente.objects.all()
    serializer_class = DescuentoClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'mes_vigente', 'porcentaje']
