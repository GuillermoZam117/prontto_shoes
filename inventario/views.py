from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Inventario, Traspaso
from .serializers import InventarioSerializer, TraspasoSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from tiendas.models import Tienda
from productos.models import Producto

# Create your views here.

class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tienda', 'producto', 'cantidad_actual', 'fecha_registro']

class TraspasoViewSet(viewsets.ModelViewSet):
    queryset = Traspaso.objects.all()
    serializer_class = TraspasoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['producto', 'tienda_origen', 'tienda_destino', 'estado', 'fecha']

class InventarioActualReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Devuelve un reporte del inventario actual agrupado por tienda y producto.
    """
    def get(self, request):
        data = []
        inventarios = Inventario.objects.select_related('tienda', 'producto').all()
        for inv in inventarios:
            data.append({
                'tienda_id': inv.tienda.id,
                'tienda_nombre': inv.tienda.nombre,
                'producto_id': inv.producto.id,
                'producto_codigo': inv.producto.codigo,
                'producto_nombre': str(inv.producto),
                'cantidad_actual': inv.cantidad_actual,
                'fecha_registro': inv.fecha_registro
            })
        return Response(data)
