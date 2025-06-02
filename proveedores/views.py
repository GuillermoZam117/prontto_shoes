from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F, Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from decimal import Decimal
from datetime import date

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Proveedor, PurchaseOrder, PurchaseOrderItem
from .serializers import ProveedorSerializer, PurchaseOrderSerializer, PurchaseOrderItemSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework.decorators import action
from rest_framework.response import Response
from requisiciones.models import DetalleRequisicion
from inventario.models import Inventario
from tiendas.models import Tienda
from productos.models import Producto

# Frontend views
@login_required
def proveedor_list(request):
    """Vista para listar proveedores con soporte para HTMX"""    # Get filter parameters
    search_query = request.GET.get('q', '')
    requiere_anticipo_param = request.GET.get('requiere_anticipo', '')
    max_return_days_min = request.GET.get('max_return_days_min', '')
    
    # Base query
    proveedores = Proveedor.objects.all()
    
    # Apply filters
    if search_query:
        proveedores = proveedores.filter(
            Q(nombre__icontains=search_query) | 
            Q(contacto__icontains=search_query)
        )
    
    # Handle requiere_anticipo filter
    if requiere_anticipo_param == 'true':
        proveedores = proveedores.filter(requiere_anticipo=True)
    elif requiere_anticipo_param == 'false':
        proveedores = proveedores.filter(requiere_anticipo=False)
    
    # Handle max_return_days filter
    if max_return_days_min:
        try:
            min_days = int(max_return_days_min)
            proveedores = proveedores.filter(max_return_days__gte=min_days)
        except ValueError:
            pass
    
    # Order results
    proveedores = proveedores.order_by('nombre')
      # Check if this is an HTMX request
    if request.headers.get('HX-Request'):
        # Return only the table partial for HTMX requests
        context = {
            'proveedores': proveedores,
            'search_query': search_query,
            'requiere_anticipo': requiere_anticipo_param,
        }
        return render(request, 'proveedores/partials/proveedor_table.html', context)
    
    # Full page render for regular requests
    # Calculate metrics for summary cards
    proveedores_anticipo = Proveedor.objects.filter(requiere_anticipo=True).count()
    proveedores_devolucion = Proveedor.objects.filter(max_return_days__gt=0).count()
    
    context = {
        'proveedores': proveedores,
        'search_query': search_query,
        'requiere_anticipo': requiere_anticipo_param,
        'proveedores_anticipo': proveedores_anticipo,
        'proveedores_devolucion': proveedores_devolucion,
    }
    
    return render(request, 'proveedores/proveedor_list.html', context)

@login_required
def proveedor_detail(request, pk):
    """Vista de detalle de un proveedor"""
    proveedor = get_object_or_404(Proveedor, pk=pk)
    
    # Get products related to this provider
    productos = Producto.objects.filter(proveedor=proveedor)
    productos_count = productos.count()
    
    # Add stock information to products
    for producto in productos:
        inventario_total = Inventario.objects.filter(producto=producto).aggregate(
            total=Sum('cantidad_actual')
        )
        producto.stock_actual = inventario_total['total'] or 0
    
    # Get purchase orders for this provider
    purchase_orders = PurchaseOrder.objects.filter(proveedor=proveedor).order_by('-fecha_creacion')
    
    # Count purchase orders by status
    purchase_orders_completed = purchase_orders.filter(estado='completado').count()
    purchase_orders_pending = purchase_orders.filter(estado='pendiente').count()
    purchase_orders_canceled = purchase_orders.filter(estado='cancelado').count()
    
    context = {
        'proveedor': proveedor,
        'productos': productos,
        'productos_count': productos_count,
        'purchase_orders': purchase_orders,
        'purchase_orders_completed': purchase_orders_completed,
        'purchase_orders_pending': purchase_orders_pending,
        'purchase_orders_canceled': purchase_orders_canceled,
    }
    
    return render(request, 'proveedores/proveedor_detail.html', context)

@login_required
def proveedor_create(request):
    """Vista para crear un nuevo proveedor"""
    if request.method == 'POST':
        try:
            # Get form data
            nombre = request.POST.get('nombre', '').strip()
            contacto = request.POST.get('contacto', '').strip()
            requiere_anticipo = request.POST.get('requiere_anticipo', '') == 'on'
            max_return_days = int(request.POST.get('max_return_days', 0) or 0)
            
            # Validate required fields
            if not nombre:
                messages.error(request, "El nombre del proveedor es obligatorio.")
                return redirect('proveedores:nuevo')
            
            # Create proveedor
            proveedor = Proveedor.objects.create(
                nombre=nombre,
                contacto=contacto,
                requiere_anticipo=requiere_anticipo,
                max_return_days=max_return_days,
                created_by=request.user
            )
            
            messages.success(request, f"Proveedor '{nombre}' creado exitosamente.")
            return redirect('proveedores:detalle', pk=proveedor.pk)
        
        except Exception as e:
            messages.error(request, f"Error al crear el proveedor: {str(e)}")
    
    context = {}
    return render(request, 'proveedores/proveedor_form.html', context)

@login_required
def proveedor_edit(request, pk):
    """Vista para editar un proveedor existente"""
    proveedor = get_object_or_404(Proveedor, pk=pk)
    
    if request.method == 'POST':
        try:
            # Get form data
            nombre = request.POST.get('nombre', '').strip()
            contacto = request.POST.get('contacto', '').strip()
            requiere_anticipo = request.POST.get('requiere_anticipo', '') == 'on'
            max_return_days = int(request.POST.get('max_return_days', 0) or 0)
            
            # Validate required fields
            if not nombre:
                messages.error(request, "El nombre del proveedor es obligatorio.")
                return redirect('proveedores:editar', pk=proveedor.pk)
            
            # Update proveedor
            proveedor.nombre = nombre
            proveedor.contacto = contacto
            proveedor.requiere_anticipo = requiere_anticipo
            proveedor.max_return_days = max_return_days
            proveedor.save()
            
            messages.success(request, f"Proveedor '{nombre}' actualizado exitosamente.")
            return redirect('proveedores:detalle', pk=proveedor.pk)
        
        except Exception as e:
            messages.error(request, f"Error al actualizar el proveedor: {str(e)}")
    
    context = {
        'proveedor': proveedor,
        'is_edit': True,
    }
    
    return render(request, 'proveedores/proveedor_form.html', context)

@login_required
def purchase_order_list(request):
    """Vista para listar órdenes de compra"""
    # Base query with related fields
    purchase_orders = PurchaseOrder.objects.select_related('proveedor', 'tienda', 'created_by')
    
    # Get filter parameters
    proveedor_id = request.GET.get('proveedor', '')
    tienda_id = request.GET.get('tienda', '')
    estado = request.GET.get('estado', '')
    
    # Apply filters
    if proveedor_id:
        purchase_orders = purchase_orders.filter(proveedor_id=proveedor_id)
    
    if tienda_id:
        purchase_orders = purchase_orders.filter(tienda_id=tienda_id)
    
    if estado:
        purchase_orders = purchase_orders.filter(estado=estado)
    
    # Get lists for filter dropdowns
    proveedores = Proveedor.objects.all()
    tiendas = Tienda.objects.all()
    
    context = {
        'purchase_orders': purchase_orders,
        'proveedores': proveedores,
        'tiendas': tiendas,
        'proveedor_id': proveedor_id,
        'tienda_id': tienda_id,
        'estado': estado,
    }
    
    return render(request, 'proveedores/purchase_order_list.html', context)

@login_required
def purchase_order_detail(request, pk):
    """Vista de detalle de una orden de compra"""
    purchase_order = get_object_or_404(PurchaseOrder.objects.select_related('proveedor', 'tienda', 'created_by'), pk=pk)
    items = purchase_order.items.select_related('producto').all()
    
    context = {
        'purchase_order': purchase_order,
        'items': items,
    }
    
    return render(request, 'proveedores/purchase_order_detail.html', context)

@login_required
def purchase_order_create(request):
    """Vista para crear una nueva orden de compra"""
    # This is a placeholder - purchase orders will need a more complex implementation
    # with item selection, quantities, etc.
    proveedores = Proveedor.objects.all()
    tiendas = Tienda.objects.all()
    
    # Pre-select provider if provided in query parameter
    selected_proveedor = request.GET.get('proveedor', '')
    
    context = {
        'proveedores': proveedores,
        'tiendas': tiendas,
        'selected_proveedor': selected_proveedor,
    }
    
    return render(request, 'proveedores/purchase_order_form.html', context)

@login_required
@require_http_methods(["POST", "DELETE"])
def proveedor_delete(request, pk):
    """Vista para eliminar un proveedor con validaciones"""
    proveedor = get_object_or_404(Proveedor, pk=pk)
    
    try:
        # Check if provider has products
        productos_count = Producto.objects.filter(proveedor=proveedor).count()
        
        if productos_count > 0:
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': False,
                    'message': f'No se puede eliminar el proveedor {proveedor.nombre}. Tiene {productos_count} producto(s) asociado(s).'
                }, status=400)
            else:
                messages.error(request, f'No se puede eliminar el proveedor {proveedor.nombre}. Tiene {productos_count} producto(s) asociado(s).')
                return redirect('proveedores:lista')
        
        # Check if provider has pending purchase orders
        ordenes_pendientes = PurchaseOrder.objects.filter(
            proveedor=proveedor, 
            estado__in=['pendiente', 'enviado']
        ).count()
        
        if ordenes_pendientes > 0:
            if request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': False,
                    'message': f'No se puede eliminar el proveedor {proveedor.nombre}. Tiene {ordenes_pendientes} orden(es) de compra pendiente(s).'
                }, status=400)
            else:
                messages.error(request, f'No se puede eliminar el proveedor {proveedor.nombre}. Tiene {ordenes_pendientes} orden(es) de compra pendiente(s).')
                return redirect('proveedores:lista')
        
        # If all validations pass, delete the provider
        nombre_proveedor = proveedor.nombre
        proveedor.delete()
        
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'message': f'Proveedor {nombre_proveedor} eliminado exitosamente.'
            })
        else:
            messages.success(request, f'Proveedor {nombre_proveedor} eliminado exitosamente.')
            return redirect('proveedores:lista')
            
    except Exception as e:
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'success': False,
                'message': f'Error al eliminar el proveedor: {str(e)}'
            }, status=500)
        else:
            messages.error(request, f'Error al eliminar el proveedor: {str(e)}')
            return redirect('proveedores:lista')

# API viewsets
@extend_schema(tags=["Proveedores"])
class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAuthenticated]

@extend_schema(tags=["Purchase Orders"])
class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['proveedor', 'estado', 'tienda', 'fecha_creacion']

    @extend_schema(
        description="Create Purchase Orders from selected Requisition Details.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'detalle_requisicion_ids': {
                        'type': 'array',
                        'items': {'type': 'integer'},
                        'description': 'List of DetalleRequisicion IDs to include in Purchase Orders'
                    },
                    'tienda_id': {
                        'type': 'integer',
                        'description': 'ID of the store placing the order'
                    }
                },
                'required': ['detalle_requisicion_ids', 'tienda_id']
            }
        },
        responses={201: PurchaseOrderSerializer(many=True), 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['post'])
    def create_from_requisitions(self, request):
        detalle_requisicion_ids = request.data.get('detalle_requisicion_ids')
        tienda_id = request.data.get('tienda_id')

        if not detalle_requisicion_ids or not tienda_id:
            return Response({"error": "Debe proporcionar una lista de IDs de detalles de requisición y el ID de la tienda."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tienda = Tienda.objects.get(id=tienda_id)
        except Tienda.DoesNotExist:
            return Response({"error": "Tienda no encontrada."}, status=status.HTTP_404_NOT_FOUND)

        requisition_details = DetalleRequisicion.objects.filter(id__in=detalle_requisicion_ids).select_related('producto__proveedor')

        if requisition_details.count() != len(detalle_requisicion_ids):
             return Response({"error": "Algunos IDs de detalles de requisición no son válidos."}, status=status.HTTP_400_BAD_REQUEST)

        # Group requisition details by supplier
        requisition_details_by_supplier = {}
        for detail in requisition_details:
            proveedor = detail.producto.proveedor
            if proveedor not in requisition_details_by_supplier:
                requisition_details_by_supplier[proveedor] = []
            requisition_details_by_supplier[proveedor].append(detail)

        created_purchase_orders = []
        errors = {}

        with transaction.atomic():
            for proveedor, details in requisition_details_by_supplier.items():
                try:
                    # Create Purchase Order for each supplier
                    purchase_order = PurchaseOrder.objects.create(
                        proveedor=proveedor,
                        tienda=tienda,
                        created_by=request.user
                    )
                    created_purchase_orders.append(purchase_order)

                    # Create Purchase Order Items
                    for detail in details:
                        PurchaseOrderItem.objects.create(
                            purchase_order=purchase_order,
                            producto=detail.producto,
                            cantidad_solicitada=detail.cantidad,
                            detalle_requisicion=detail
                        )

                except Exception as e:
                    errors[proveedor.nombre] = f"Error creating Purchase Order for {proveedor.nombre}: {e}"
                    transaction.set_rollback(True)
                    return Response({"message": "Error creating purchase orders.", "error_details": errors}, status=status.HTTP_400_BAD_REQUEST)

        if errors:
            return Response({"message": "Purchase Orders created with errors.", "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = self.get_serializer(created_purchase_orders, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        description="Record received quantities for Purchase Order Items and update inventory.",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'received_items': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'purchase_order_item_id': {'type': 'integer', 'description': 'ID of the PurchaseOrderItem'},
                                'cantidad_recibida': {'type': 'integer', 'description': 'Quantity received for this item'}
                            },
                            'required': ['purchase_order_item_id', 'cantidad_recibida']
                        },
                        'description': 'List of items received with quantities.'
                    }
                },
                'required': ['received_items']
            }
        },
        responses={200: PurchaseOrderSerializer, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT}
    )
    @action(detail=True, methods=['post'])
    def receive_items(self, request, pk=None):
        """
        Record received quantities for items in a purchase order and update inventory.
        """
        purchase_order = self.get_object()
        received_items_data = request.data.get('received_items')

        if not received_items_data:
            return Response({"error": "Debe proporcionar una lista de items recibidos."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            for item_data in received_items_data:
                item_id = item_data.get('purchase_order_item_id')
                cantidad_recibida = item_data.get('cantidad_recibida')

                if item_id is None or cantidad_recibida is None:
                    transaction.set_rollback(True)
                    return Response({"error": "Cada item recibido debe tener 'purchase_order_item_id' y 'cantidad_recibida'."}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    purchase_order_item = PurchaseOrderItem.objects.select_for_update().get(
                        id=item_id,
                        purchase_order=purchase_order
                    )
                except PurchaseOrderItem.DoesNotExist:
                    transaction.set_rollback(True)
                    return Response({"error": f"Purchase Order Item con ID {item_id} no encontrado en esta orden de compra."}, status=status.HTTP_404_NOT_FOUND)

                # Update received quantity
                purchase_order_item.cantidad_recibida = cantidad_recibida
                purchase_order_item.save()

                # Update inventory in the destination store of the Purchase Order
                store_inventory, created = Inventario.objects.select_for_update().get_or_create(
                    tienda=purchase_order.tienda,
                    producto=purchase_order_item.producto,
                    defaults={'cantidad_actual': 0}
                )
                store_inventory.cantidad_actual = F('cantidad_actual') + cantidad_recibida
                store_inventory.save()

        purchase_order.refresh_from_db()
        serializer = self.get_serializer(purchase_order)
        return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(tags=["Purchase Orders"])
class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['purchase_order', 'producto', 'detalle_requisicion']
