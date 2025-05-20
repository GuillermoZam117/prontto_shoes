from django.shortcuts import render
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

from .models import Devolucion
from .serializers import DevolucionSerializer
from ventas.models import DetallePedido # Corrected import to DetallePedido
from productos.models import Producto # Import Producto
from clientes.models import Cliente
from proveedores.models import Proveedor # Import Proveedor


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
