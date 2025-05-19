from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Pedido, DetallePedido
from .serializers import PedidoSerializer, DetallePedidoSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.views import APIView
from rest_framework.response import Response
from clientes.models import Cliente
from productos.models import Producto
from rest_framework.pagination import LimitOffsetPagination
from django.utils.dateparse import parse_date

@extend_schema(tags=["Ventas"])
class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'fecha', 'estado', 'tienda', 'tipo']

@extend_schema(tags=["Ventas"])
class DetallePedidoViewSet(viewsets.ModelViewSet):
    queryset = DetallePedido.objects.all()
    serializer_class = DetallePedidoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['pedido', 'producto']

@extend_schema(
    tags=["Reportes"],
    parameters=[
        OpenApiParameter("cliente_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Filtrar por ID de cliente"),
        OpenApiParameter("fecha_desde", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False, description="Filtrar pedidos desde esta fecha (YYYY-MM-DD)"),
        OpenApiParameter("fecha_hasta", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False, description="Filtrar pedidos hasta esta fecha (YYYY-MM-DD)"),
        OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Límite de resultados por página (paginación)"),
        OpenApiParameter("offset", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Offset para paginación"),
    ],
    description="Devuelve un reporte de productos apartados por cliente (pedidos pendientes). Permite filtrar por cliente y rango de fechas, y soporta paginación."
)
class ApartadosPorClienteReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    """
    Devuelve un reporte de productos apartados por cliente (pedidos pendientes).
    """
    def get(self, request):
        # Obtener clientes y aplicar filtro si se especifica cliente_id
        clientes_qs = Cliente.objects.all()
        cliente_id = request.query_params.get("cliente_id")
        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")
        
        if cliente_id:
            clientes_qs = clientes_qs.filter(id=cliente_id)

        data = []
        for cliente in clientes_qs:
            # Filtrar pedidos pendientes del cliente
            pedidos_pendientes = cliente.pedidos.filter(estado='pendiente')
            if fecha_desde:
                pedidos_pendientes = pedidos_pendientes.filter(fecha__gte=parse_date(fecha_desde))
            if fecha_hasta:
                pedidos_pendientes = pedidos_pendientes.filter(fecha__lte=parse_date(fecha_hasta))

            # Si el cliente tiene pedidos pendientes, incluirlo en el reporte
            if pedidos_pendientes.exists():
                total_apartado = 0
                productos_apartados = []
                
                # Agrupar detalles por pedido
                for pedido in pedidos_pendientes:
                    detalles = DetallePedido.objects.filter(pedido=pedido).select_related('producto')
                    
                    for detalle in detalles:
                        total_apartado += detalle.subtotal
                        productos_apartados.append({
                            'producto_id': detalle.producto.id,
                            'codigo': detalle.producto.codigo,
                            'marca': detalle.producto.marca,
                            'modelo': detalle.producto.modelo,
                            'color': detalle.producto.color,
                            'propiedad': detalle.producto.propiedad,
                            'cantidad': detalle.cantidad,
                            'precio_unitario': detalle.precio_unitario,
                            'subtotal': detalle.subtotal,
                            'fecha_apartado': pedido.fecha,
                            'pedido_id': pedido.id
                        })

                data.append({
                    'cliente_id': cliente.id,
                    'cliente_nombre': cliente.nombre,
                    'tienda_id': cliente.tienda.id,
                    'tienda_nombre': cliente.tienda.nombre,
                    'total_apartado': total_apartado,
                    'cantidad_productos': len(productos_apartados),
                    'productos': productos_apartados,
                    'saldo_a_favor': cliente.saldo_a_favor,
                    'descuento_actual': cliente.descuento_actual
                })

        # Aplicar paginación si está configurada
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(data, request)
        
        if page is not None:
            return paginator.get_paginated_response(page)
            
        return Response(data)

@extend_schema(
    tags=["Reportes"],
    parameters=[
        OpenApiParameter("cliente_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Filtrar por ID de cliente"),
        OpenApiParameter("tienda_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Filtrar por ID de tienda"),
        OpenApiParameter("fecha_desde", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False, description="Filtrar pedidos desde esta fecha (YYYY-MM-DD)"),
        OpenApiParameter("fecha_hasta", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False, description="Filtrar pedidos hasta esta fecha (YYYY-MM-DD)"),
        OpenApiParameter("estado", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False, description="Filtrar por estado (pendiente/completado)"),
        OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Límite de resultados por página"),
        OpenApiParameter("offset", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False, description="Offset para paginación"),
    ],
    description="Devuelve un reporte de pedidos surtidos y pendientes, agrupados por estado. Permite filtrar por cliente, tienda, fechas y estado."
)
class PedidosPorSurtirReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get(self, request):
        # Obtener y validar parámetros
        cliente_id = request.query_params.get("cliente_id")
        tienda_id = request.query_params.get("tienda_id")
        fecha_desde = request.query_params.get("fecha_desde")
        fecha_hasta = request.query_params.get("fecha_hasta")
        estado = request.query_params.get("estado")

        # Construir query base con optimización de joins
        pedidos = Pedido.objects.select_related(
            'cliente',
            'tienda'
        ).prefetch_related(
            'detallepedido_set__producto',
            'detallepedido_set__producto__proveedor'
        )

        # Aplicar filtros
        if cliente_id:
            pedidos = pedidos.filter(cliente_id=cliente_id)
        if tienda_id:
            pedidos = pedidos.filter(tienda_id=tienda_id)
        if fecha_desde:
            pedidos = pedidos.filter(fecha__gte=parse_date(fecha_desde))
        if fecha_hasta:
            pedidos = pedidos.filter(fecha__lte=parse_date(fecha_hasta))
        if estado:
            pedidos = pedidos.filter(estado=estado)

        # Agrupar pedidos por estado
        resumen = {
            'pendientes': {
                'total_pedidos': 0,
                'monto_total': 0,
                'pedidos': []
            },
            'completados': {
                'total_pedidos': 0,
                'monto_total': 0,
                'pedidos': []
            }
        }

        for pedido in pedidos:
            estado_grupo = 'completados' if pedido.estado == 'completado' else 'pendientes'
            
            # Construir lista de productos del pedido
            productos = []
            for detalle in pedido.detallepedido_set.all():
                productos.append({
                    'producto_id': detalle.producto.id,
                    'codigo': detalle.producto.codigo,
                    'marca': detalle.producto.marca,
                    'modelo': detalle.producto.modelo,
                    'color': detalle.producto.color,
                    'propiedad': detalle.producto.propiedad,
                    'proveedor': detalle.producto.proveedor.nombre,
                    'cantidad': detalle.cantidad,
                    'precio_unitario': float(detalle.precio_unitario),
                    'subtotal': float(detalle.subtotal)
                })

            # Construir información del pedido
            pedido_info = {
                'pedido_id': pedido.id,
                'fecha': pedido.fecha,
                'cliente': {
                    'id': pedido.cliente.id,
                    'nombre': pedido.cliente.nombre
                },
                'tienda': {
                    'id': pedido.tienda.id,
                    'nombre': pedido.tienda.nombre
                },
                'tipo': pedido.tipo,
                'estado': pedido.estado,
                'total': float(pedido.total),
                'descuento_aplicado': float(pedido.descuento_aplicado),
                'productos': productos
            }

            # Actualizar totales del grupo
            resumen[estado_grupo]['pedidos'].append(pedido_info)
            resumen[estado_grupo]['total_pedidos'] += 1
            resumen[estado_grupo]['monto_total'] += float(pedido.total)

        # Preparar datos para la respuesta
        data = {
            'totales': {
                'total_pedidos': resumen['pendientes']['total_pedidos'] + resumen['completados']['total_pedidos'],
                'monto_total': resumen['pendientes']['monto_total'] + resumen['completados']['monto_total']
            },
            'pendientes': resumen['pendientes'],
            'completados': resumen['completados']
        }

        # Aplicar paginación al resultado final
        paginator = self.pagination_class()
        page = paginator.paginate_queryset([data], request)
        
        if page is not None:
            return paginator.get_paginated_response(page)
            
        return Response(data)
