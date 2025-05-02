from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Pedido, DetallePedido
from .serializers import PedidoSerializer, DetallePedidoSerializer
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from clientes.models import Cliente
from productos.models import Producto

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

class ApartadosPorClienteReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Devuelve un reporte de productos apartados por cliente (pedidos pendientes).
    """
    def get(self, request):
        data = []
        clientes = Cliente.objects.all()
        for cliente in clientes:
            pedidos_pendientes = cliente.pedidos.filter(estado='pendiente')
            detalles = DetallePedido.objects.filter(pedido__in=pedidos_pendientes)
            if detalles.exists():
                productos = []
                for det in detalles:
                    productos.append({
                        'producto_id': det.producto.id,
                        'codigo': det.producto.codigo,
                        'nombre': str(det.producto),
                        'cantidad': det.cantidad,
                        'estado_pedido': det.pedido.estado,
                        'pedido_id': det.pedido.id
                    })
                data.append({
                    'cliente_id': cliente.id,
                    'cliente_nombre': cliente.nombre,
                    'productos_apartados': productos
                })
        return Response(data)

class PedidosPorSurtirReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Devuelve un reporte de pedidos por surtir (estado pendiente).
    """
    def get(self, request):
        data = []
        pedidos = Pedido.objects.filter(estado='pendiente')
        for pedido in pedidos:
            detalles = DetallePedido.objects.filter(pedido=pedido)
            productos = []
            for det in detalles:
                productos.append({
                    'producto_id': det.producto.id,
                    'codigo': det.producto.codigo,
                    'nombre': str(det.producto),
                    'cantidad': det.cantidad
                })
            data.append({
                'pedido_id': pedido.id,
                'cliente_id': pedido.cliente.id,
                'cliente_nombre': pedido.cliente.nombre,
                'tienda_id': pedido.tienda.id,
                'tienda_nombre': str(pedido.tienda),
                'fecha': pedido.fecha,
                'productos': productos
            })
        return Response(data)
