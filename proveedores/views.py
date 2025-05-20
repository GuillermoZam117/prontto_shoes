from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Proveedor, PurchaseOrder, PurchaseOrderItem
from .serializers import ProveedorSerializer, PurchaseOrderSerializer, PurchaseOrderItemSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from requisiciones.models import DetalleRequisicion
from django.db.models import Sum, F
from inventario.models import Inventario
from tiendas.models import Tienda

# Create your views here.

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
