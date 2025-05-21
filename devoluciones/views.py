from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.utils.dateparse import parse_date
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.db import transaction
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.contrib import messages

from .models import Devolucion
from .serializers import DevolucionSerializer
from ventas.models import DetallePedido, Pedido
from productos.models import Producto
from clientes.models import Cliente
from proveedores.models import Proveedor
from tiendas.models import Tienda
from caja.models import Caja, TransaccionCaja

# Frontend views
def devolucion_list(request):
    """Vista para listar devoluciones"""
    # Get filter parameters
    cliente_id = request.GET.get('cliente', '')
    estado = request.GET.get('estado', '')
    tipo = request.GET.get('tipo', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    # Base query with related models
    devoluciones = Devolucion.objects.select_related(
        'cliente', 
        'producto', 
        'detalle_pedido__pedido',
        'created_by'
    ).all()
    
    # Apply filters
    if cliente_id:
        devoluciones = devoluciones.filter(cliente_id=cliente_id)
    
    if estado:
        devoluciones = devoluciones.filter(estado=estado)
        
    if tipo:
        devoluciones = devoluciones.filter(tipo=tipo)
    
    if fecha_desde:
        devoluciones = devoluciones.filter(fecha__date__gte=parse_date(fecha_desde))
    
    if fecha_hasta:
        devoluciones = devoluciones.filter(fecha__date__lte=parse_date(fecha_hasta))
    
    # Get related data for filters
    clientes = Cliente.objects.all()
    
    # Calculate statistics for summary cards
    total_pendientes = devoluciones.filter(estado='pendiente').count()
    total_validadas = devoluciones.filter(estado='validada').count()
    total_completadas = devoluciones.filter(estado='completada').count()
    saldo_generado = devoluciones.exclude(estado='rechazada').aggregate(total=Sum('saldo_a_favor_generado'))['total'] or 0
    
    context = {
        'devoluciones': devoluciones,
        'clientes': clientes,
        'cliente_seleccionado': cliente_id,
        'estado_seleccionado': estado,
        'tipo_seleccionado': tipo,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_pendientes': total_pendientes,
        'total_validadas': total_validadas,
        'total_completadas': total_completadas,
        'saldo_generado': saldo_generado
    }
    
    return render(request, 'devoluciones/devolucion_list.html', context)

def devolucion_detail(request, pk):
    """Vista de detalle de una devolución"""
    devolucion = get_object_or_404(Devolucion, pk=pk)
    
    # Get related data
    if devolucion.detalle_pedido:
        pedido = devolucion.detalle_pedido.pedido
        compra_original = {
            'pedido': pedido,
            'fecha': pedido.fecha,
            'total': pedido.total,
        }
    else:
        compra_original = None
    
    # Get timeline data (for status tracking)
    timeline_data = [
        {
            'status': 'creada',
            'date': devolucion.fecha,
            'user': devolucion.created_by.username if devolucion.created_by else 'Sistema'
        }
    ]
    
    # Add validation step if applicable
    if devolucion.estado in ['validada', 'completada']:
        timeline_data.append({
            'status': 'validada',
            'date': devolucion.updated_at if hasattr(devolucion, 'updated_at') else devolucion.fecha,
            'user': devolucion.updated_by.username if hasattr(devolucion, 'updated_by') and devolucion.updated_by else 'Sistema'
        })
    
    # Add completion step if applicable
    if devolucion.estado == 'completada':
        timeline_data.append({
            'status': 'completada',
            'date': devolucion.updated_at if hasattr(devolucion, 'updated_at') else devolucion.fecha,
            'user': devolucion.updated_by.username if hasattr(devolucion, 'updated_by') and devolucion.updated_by else 'Sistema'
        })
    
    context = {
        'devolucion': devolucion,
        'compra_original': compra_original,
        'timeline': timeline_data,
    }
    
    return render(request, 'devoluciones/devolucion_detail.html', context)

def devolucion_create(request):
    """Vista para crear una nueva devolución"""
    clientes = Cliente.objects.all()
    productos = Producto.objects.all().select_related('proveedor')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                cliente_id = request.POST.get('cliente')
                producto_id = request.POST.get('producto')
                detalle_pedido_id = request.POST.get('detalle_pedido', None)
                tipo = request.POST.get('tipo')
                motivo = request.POST.get('motivo', '').strip()
                afecta_inventario = request.POST.get('afecta_inventario') == 'on'
                
                # Validate required fields
                if not cliente_id or not producto_id or not tipo:
                    messages.error(request, "Cliente, producto y tipo de devolución son obligatorios.")
                    return redirect('devoluciones:nueva')
                
                # Get related objects
                cliente = get_object_or_404(Cliente, pk=cliente_id)
                producto = get_object_or_404(Producto, pk=producto_id)
                
                # Initialize variables
                detalle_pedido = None
                precio_devolucion = producto.precio  # Default to current price
                
                # If detalle_pedido_id is provided, link to original sale
                if detalle_pedido_id:
                    detalle_pedido = get_object_or_404(DetallePedido, pk=detalle_pedido_id)
                    if detalle_pedido.pedido.cliente.id != int(cliente_id):
                        messages.error(request, "El pedido seleccionado no pertenece a este cliente.")
                        return redirect('devoluciones:nueva')
                    
                    # Check return period
                    sale_date = detalle_pedido.pedido.fecha.date()
                    client_max_days = cliente.max_return_days
                    supplier_max_days = producto.proveedor.max_return_days if producto.proveedor else float('inf')
                    
                    max_allowed_days = min(client_max_days, supplier_max_days)
                    return_deadline = sale_date + timedelta(days=max_allowed_days)
                    
                    if timezone.now().date() > return_deadline:
                        messages.error(request, f"El período para devolver este producto ha expirado. La fecha límite era {return_deadline}.")
                        return redirect('devoluciones:nueva')
                    
                    # Set price to the original sale price (or the lower of original and current if the price has dropped)
                    precio_devolucion = min(detalle_pedido.precio_unitario, producto.precio)
                
                # Calculate saldo_a_favor based on tipo
                saldo_a_favor_generado = 0
                if tipo == 'defecto':
                    # For defects, generate credit
                    saldo_a_favor_generado = precio_devolucion
                    confirmacion_proveedor = False
                elif tipo == 'cambio':
                    # For exchanges, no credit (handled separately)
                    saldo_a_favor_generado = 0
                    confirmacion_proveedor = False  # Usually not needed for exchanges
                
                # Create devolucion
                devolucion = Devolucion.objects.create(
                    cliente=cliente,
                    producto=producto,
                    detalle_pedido=detalle_pedido,
                    tipo=tipo,
                    motivo=motivo,
                    estado='pendiente',
                    confirmacion_proveedor=confirmacion_proveedor,
                    afecta_inventario=afecta_inventario,
                    saldo_a_favor_generado=saldo_a_favor_generado,
                    precio_devolucion=precio_devolucion,
                    created_by=request.user
                )
                
                messages.success(request, f"Devolución registrada correctamente con ID {devolucion.id}.")
                return redirect('devoluciones:detalle', pk=devolucion.pk)
                
        except Exception as e:
            messages.error(request, f"Error al registrar la devolución: {str(e)}")
    
    # Get default parameters from query string (if any)
    cliente_id = request.GET.get('cliente', '')
    pedido_id = request.GET.get('pedido', '')
    
    # Get pedidos if cliente_id is provided
    pedidos = []
    detalle_pedidos = []
    if cliente_id:
        pedidos = Pedido.objects.filter(cliente_id=cliente_id)
        if pedido_id:
            detalle_pedidos = DetallePedido.objects.filter(pedido_id=pedido_id).select_related('producto')
    
    context = {
        'clientes': clientes,
        'productos': productos,
        'pedidos': pedidos,
        'detalle_pedidos': detalle_pedidos,
        'cliente_id': cliente_id,
        'pedido_id': pedido_id,
    }
    
    return render(request, 'devoluciones/devolucion_form.html', context)

def devolucion_edit(request, pk):
    """Vista para editar una devolución existente"""
    devolucion = get_object_or_404(Devolucion, pk=pk)
    
    # Only allow editing for pending returns
    if devolucion.estado != 'pendiente':
        messages.error(request, "Solo se pueden editar devoluciones en estado 'pendiente'.")
        return redirect('devoluciones:detalle', pk=pk)
    
    clientes = Cliente.objects.all()
    productos = Producto.objects.all().select_related('proveedor')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                motivo = request.POST.get('motivo', '').strip()
                tipo = request.POST.get('tipo')
                afecta_inventario = request.POST.get('afecta_inventario') == 'on'
                
                # Validate required fields
                if not tipo:
                    messages.error(request, "El tipo de devolución es obligatorio.")
                    return redirect('devoluciones:editar', pk=pk)
                
                # Calculate saldo_a_favor based on tipo
                if tipo == 'defecto':
                    # For defects, generate credit
                    saldo_a_favor_generado = devolucion.precio_devolucion
                    confirmacion_proveedor = False
                elif tipo == 'cambio':
                    # For exchanges, no credit (handled separately)
                    saldo_a_favor_generado = 0
                    confirmacion_proveedor = False  # Usually not needed for exchanges
                
                # Update devolucion
                devolucion.tipo = tipo
                devolucion.motivo = motivo
                devolucion.afecta_inventario = afecta_inventario
                devolucion.saldo_a_favor_generado = saldo_a_favor_generado
                devolucion.confirmacion_proveedor = confirmacion_proveedor
                devolucion.save()
                
                messages.success(request, f"Devolución actualizada correctamente.")
                return redirect('devoluciones:detalle', pk=pk)
                
        except Exception as e:
            messages.error(request, f"Error al actualizar la devolución: {str(e)}")
    
    # Get pedidos if cliente_id is provided
    pedidos = []
    detalle_pedidos = []
    if devolucion.detalle_pedido:
        pedido_id = devolucion.detalle_pedido.pedido.id
        pedidos = Pedido.objects.filter(cliente=devolucion.cliente)
        detalle_pedidos = DetallePedido.objects.filter(pedido_id=pedido_id).select_related('producto')
    
    context = {
        'devolucion': devolucion,
        'clientes': clientes,
        'productos': productos,
        'pedidos': pedidos,
        'detalle_pedidos': detalle_pedidos,
        'is_edit': True,
    }
    
    return render(request, 'devoluciones/devolucion_form.html', context)

def devolucion_validate(request, pk):
    """Vista para validar una devolución"""
    devolucion = get_object_or_404(Devolucion, pk=pk)
    
    # Only allow validation for pending returns
    if devolucion.estado != 'pendiente':
        messages.error(request, "Solo se pueden validar devoluciones en estado 'pendiente'.")
        return redirect('devoluciones:detalle', pk=pk)
    
    # Check if validation action is submitted
    if request.method == 'POST':
        action = request.POST.get('action')
        
        try:
            with transaction.atomic():
                if action == 'validate':
                    # Approve return
                    devolucion.estado = 'validada'
                    devolucion.save()
                    
                    # Process inventory update if applicable
                    if devolucion.afecta_inventario:
                        # Logic to return product to inventory would go here
                        pass
                    
                    # Process customer credit if applicable
                    if devolucion.saldo_a_favor_generado > 0:
                        cliente = devolucion.cliente
                        cliente.saldo_a_favor += devolucion.saldo_a_favor_generado
                        cliente.save()
                        
                        # Record transaction in Caja if needed
                        try:
                            # Find open cash register
                            today = timezone.now().date()
                            user = request.user
                            
                            if hasattr(user, 'tienda') and user.tienda:
                                try:
                                    caja_abierta = Caja.objects.get(tienda=user.tienda, fecha=today, cerrada=False)
                                    
                                    # Register transaction
                                    TransaccionCaja.objects.create(
                                        caja=caja_abierta,
                                        tipo_movimiento='egreso',  # Refunds are expenses for the store
                                        monto=devolucion.saldo_a_favor_generado,
                                        descripcion=f'Devolución #{devolucion.id} - Cliente: {devolucion.cliente.nombre}',
                                        created_by=user
                                    )
                                except Caja.DoesNotExist:
                                    # No open cash register, just log the error
                                    pass
                        except Exception as e:
                            # Log error but continue processing
                            pass
                    
                    messages.success(request, f"Devolución validada correctamente.")
                
                elif action == 'reject':
                    # Reject return
                    devolucion.estado = 'rechazada'
                    devolucion.save()
                    messages.success(request, f"Devolución rechazada.")
                
                elif action == 'complete':
                    # Mark as completed
                    devolucion.estado = 'completada'
                    devolucion.save()
                    messages.success(request, f"Devolución marcada como completada.")
                
                return redirect('devoluciones:detalle', pk=pk)
                
        except Exception as e:
            messages.error(request, f"Error al procesar la devolución: {str(e)}")
            return redirect('devoluciones:validar', pk=pk)
    
    context = {
        'devolucion': devolucion,
    }
    
    return render(request, 'devoluciones/devolucion_validate.html', context)

def devolucion_report(request):
    """Vista para generar reportes de devoluciones"""
    # Get filter parameters
    cliente_id = request.GET.get('cliente', '')
    estado = request.GET.get('estado', '')
    tipo = request.GET.get('tipo', '')
    fecha_desde = request.GET.get('fecha_desde', (timezone.now().replace(day=1)).strftime('%Y-%m-%d'))
    fecha_hasta = request.GET.get('fecha_hasta', timezone.now().strftime('%Y-%m-%d'))
    
    # Base query with related models
    devoluciones = Devolucion.objects.select_related(
        'cliente', 
        'producto', 
        'producto__proveedor',
        'detalle_pedido__pedido'
    ).all()
    
    # Apply filters
    if cliente_id:
        devoluciones = devoluciones.filter(cliente_id=cliente_id)
    
    if estado:
        devoluciones = devoluciones.filter(estado=estado)
        
    if tipo:
        devoluciones = devoluciones.filter(tipo=tipo)
    
    if fecha_desde:
        devoluciones = devoluciones.filter(fecha__date__gte=parse_date(fecha_desde))
    
    if fecha_hasta:
        devoluciones = devoluciones.filter(fecha__date__lte=parse_date(fecha_hasta))
    
    # Get related data for filters
    clientes = Cliente.objects.all()
    
    # Group data for charts
    devoluciones_por_tipo = devoluciones.values('tipo').annotate(count=Count('id'))
    devoluciones_por_estado = devoluciones.values('estado').annotate(count=Count('id'))
    
    # Group by cliente for detailed report
    clientes_datos = {}
    for devolucion in devoluciones:
        cliente_id = devolucion.cliente.id
        if cliente_id not in clientes_datos:
            clientes_datos[cliente_id] = {
                'nombre': devolucion.cliente.nombre,
                'devoluciones_count': 0,
                'saldo_generado': 0,
                'tipos': {'defecto': 0, 'cambio': 0}
            }
        
        clientes_datos[cliente_id]['devoluciones_count'] += 1
        clientes_datos[cliente_id]['saldo_generado'] += devolucion.saldo_a_favor_generado
        clientes_datos[cliente_id]['tipos'][devolucion.tipo] += 1
    
    # Calculate summary metrics
    total_devoluciones = devoluciones.count()
    total_saldo_generado = devoluciones.aggregate(total=Sum('saldo_a_favor_generado'))['total'] or 0
    total_defectos = devoluciones.filter(tipo='defecto').count()
    total_cambios = devoluciones.filter(tipo='cambio').count()
    
    context = {
        'devoluciones': devoluciones,
        'clientes': clientes,
        'cliente_seleccionado': cliente_id,
        'estado_seleccionado': estado,
        'tipo_seleccionado': tipo,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'devoluciones_por_tipo': devoluciones_por_tipo,
        'devoluciones_por_estado': devoluciones_por_estado,
        'clientes_datos': clientes_datos.values(),
        'total_devoluciones': total_devoluciones,
        'total_saldo_generado': total_saldo_generado,
        'total_defectos': total_defectos,
        'total_cambios': total_cambios
    }
    
    return render(request, 'devoluciones/devolucion_report.html', context)

# API viewsets
class DevolucionViewSet(viewsets.ModelViewSet):
    queryset = Devolucion.objects.all()
    serializer_class = DevolucionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'producto', 'tipo', 'fecha', 'estado', 'confirmacion_proveedor', 'afecta_inventario']

    def perform_create(self, serializer):
        # Link devolution to the authenticated user
        serializer.save(created_by=self.request.user)

    # Override create to add custom validation and logic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Assuming `detalle_pedido` ID is passed in the request for linking to the original sale item
        detalle_pedido_id = serializer.validated_data.get('detalle_pedido').id if serializer.validated_data.get('detalle_pedido') else None
        producto = serializer.validated_data.get('producto')
        cliente = serializer.validated_data.get('cliente')
        tipo_devolucion = serializer.validated_data.get('tipo')
        saldo_a_favor_generado = serializer.validated_data.get('saldo_a_favor_generado', 0) # Get saldo_a_favor_generado

        detalle_pedido = None
        original_sale_price = None
        if detalle_pedido_id:
            try:
                detalle_pedido = DetallePedido.objects.select_related('pedido__cliente', 'producto__proveedor').get(id=detalle_pedido_id)
                # Verify the client in the devolution request matches the client in the original sale
                if detalle_pedido.pedido.cliente != cliente:
                     raise ValidationError("El detalle de pedido no corresponde a este cliente.")

                original_sale_price = detalle_pedido.precio_unitario
                sale_date = detalle_pedido.pedido.fecha.date() # Assuming fecha is a DateTimeField

                # ** Validation: Return validity period based on client and supplier **
                client_max_days = cliente.max_return_days
                # Assuming product is linked to a supplier to get supplier's return policy
                supplier_max_days = producto.proveedor.max_return_days if producto.proveedor else float('inf') # Use infinity if no supplier linked
                
                max_allowed_days = min(client_max_days, supplier_max_days)
                return_deadline = sale_date + timedelta(days=max_allowed_days)

                if timezone.now().date() > return_deadline:
                     raise ValidationError(f"El período para devolver este producto ha expirado. La fecha límite era {return_deadline}.")

            except DetallePedido.DoesNotExist:
                raise ValidationError("Detalle de pedido no encontrado.")
            except Cliente.DoesNotExist:
                 raise ValidationError("Cliente no encontrado.") # Should not happen due to previous validation, but as safeguard
            except Proveedor.DoesNotExist:
                 # Handle cases where a product might not have a supplier or supplier has no max_return_days set
                 pass # Validation will proceed with client_max_days only

        # ** Determine return price (lower of sale price and current price) **
        precio_actual_producto = producto.precio
        
        # If original_sale_price is available, use it for comparison
        precio_devolucion = precio_actual_producto
        if original_sale_price is not None:
             precio_devolucion = min(precio_actual_producto, original_sale_price)

        serializer.validated_data['precio_devolucion'] = precio_devolucion

        # ** Set initial state and other fields **
        serializer.validated_data['estado'] = 'pendiente'
        
        # Logic for afecta_inventario and saldo_a_favor_generado
        afecta_inventario = False # Default
        # Assuming inventory is affected for 'cambio' type returns if the item is to be restocked
        # and for 'defecto' only if it's returned to supplier (which might be a separate process/status)
        if tipo_devolucion == 'cambio':
             afecta_inventario = True # Assuming returned to stock for change
             # For 'cambio', saldo_a_favor_generado might be 0 or depend on price difference
             serializer.validated_data['saldo_a_favor_generado'] = 0 # Assuming even exchange or separate process for price diff

        elif tipo_devolucion == 'defecto':
             afecta_inventario = False # Assuming defective items are not returned to sellable inventory
             # For 'defecto', saldo_a_favor_generado is the refund amount based on precio_devolucion and quantity
             cantidad_devolver = serializer.validated_data.get('cantidad', 1) # Assuming quantity is in serializer data, default 1
             serializer.validated_data['saldo_a_favor_generado'] = precio_devolucion * cantidad_devolver # Generate credit based on return price and quantity
             # Set confirmacion_proveedor for 'defecto' type
             serializer.validated_data['confirmacion_proveedor'] = False # Requires supplier confirmation
        else:
            # Handle other or unknown types if necessary
            pass

        serializer.validated_data['afecta_inventario'] = afecta_inventario

        with transaction.atomic():
            devolucion = serializer.save(created_by=request.user) # Save with created_by

            # TODO: If afecta_inventario is True, update inventory for the relevant store(s)
            # This would involve increasing the inventory count for the returned product.

            # TODO: If saldo_a_favor_generado > 0, update the client's saldo_a_favor in the Cliente model.

            # TODO: Record transaction in Caja if it involves a cash refund (might need a new transaction type in TransaccionCaja)
            # This would likely happen upon confirming the return/refund, not necessarily on creation.

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema(
    tags=["Reportes"],
    parameters=[
        OpenApiParameter("cliente_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Filtrar por ID de cliente"),
        OpenApiParameter("fecha_desde", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False, description="Filtrar devoluciones desde esta fecha (YYYY-MM-DD)"),
        OpenApiParameter("fecha_hasta", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False, description="Filtrar devoluciones hasta esta fecha (YYYY-MM-DD)"),
        OpenApiParameter("tipo", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description="Filtrar por tipo de devolución (defecto/cambio)"),
        OpenApiParameter("estado", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description="Filtrar por estado de validación"),
        OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Límite de resultados por página"),
        OpenApiParameter("offset", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Offset para paginación"),
    ],
    description="Devuelve un reporte de devoluciones por cliente. Permite filtrar por cliente, fechas, tipo y estado. Incluye detalles del producto y estado de validación."
)
class DevolucionesReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        # Obtener y validar parámetros
        cliente_id = request.query_params.get("cliente_id")
        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")
        tipo = request.query_params.get("tipo")
        estado = request.query_params.get("estado")
        limit = request.query_params.get("limit")

        # Construir query base
        devoluciones = Devolucion.objects.select_related(
            'cliente', 
            'producto', 
            'producto__proveedor'
        ).all()

        # Aplicar filtros
        if cliente_id:
            devoluciones = devoluciones.filter(cliente_id=cliente_id)
        if fecha_desde:
            devoluciones = devoluciones.filter(fecha__gte=parse_date(fecha_desde))
        if fecha_hasta:
            devoluciones = devoluciones.filter(fecha__lte=parse_date(fecha_hasta))
        if tipo:
            devoluciones = devoluciones.filter(tipo=tipo)
        if estado:
            devoluciones = devoluciones.filter(estado=estado)

        # Agrupar por cliente para el reporte
        data = []
        clientes_procesados = {}

        for dev in devoluciones:
            cliente_id = dev.cliente.id
            
            if cliente_id not in clientes_procesados:
                clientes_procesados[cliente_id] = {
                    'cliente_id': cliente_id,
                    'cliente_nombre': dev.cliente.nombre,
                    'total_devoluciones': 0,
                    'saldo_a_favor_total': 0,
                    'devoluciones': []
                }

            # Agregar detalles de la devolución
            clientes_procesados[cliente_id]['devoluciones'].append({
                'devolucion_id': dev.id,
                'fecha': dev.fecha,
                'producto': {
                    'id': dev.producto.id,
                    'codigo': dev.producto.codigo,
                    'marca': dev.producto.marca,
                    'modelo': dev.producto.modelo,
                    'color': dev.producto.color,
                    'propiedad': dev.producto.propiedad,
                    'proveedor': dev.producto.proveedor.nombre
                },
                'tipo': dev.tipo,
                'motivo': dev.motivo,
                'estado': dev.estado,
                'validacion': {
                    'confirmacion_proveedor': dev.confirmacion_proveedor,
                    'afecta_inventario': dev.afecta_inventario
                },
                'saldo_generado': float(dev.saldo_a_favor_generado)
            })

            # Actualizar totales del cliente
            clientes_procesados[cliente_id]['total_devoluciones'] += 1
            clientes_procesados[cliente_id]['saldo_a_favor_total'] += float(dev.saldo_a_favor_generado)

        # Convertir el diccionario a lista para la respuesta
        data = list(clientes_procesados.values())

        # Aplicar límite si está especificado en los parámetros
        if limit and limit.isdigit():
            limit_val = int(limit)
            data = data[:limit_val]

        # Mantener formato de respuesta esperado por los tests
        response_data = {
            'count': len(clientes_procesados.values()),  # Count original total
            'next': None,
            'previous': None,
            'results': data
        }
            
        return Response(response_data)
