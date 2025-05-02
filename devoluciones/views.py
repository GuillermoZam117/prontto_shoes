from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Devolucion
from .serializers import DevolucionSerializer

class DevolucionViewSet(viewsets.ModelViewSet):
    queryset = Devolucion.objects.all()
    serializer_class = DevolucionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'producto', 'tipo', 'fecha', 'estado', 'confirmacion_proveedor', 'afecta_inventario']

class DevolucionesReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Devuelve un reporte de devoluciones realizadas, mostrando cliente, producto, tipo, motivo, fecha y estado.
    """
    def get(self, request):
        from .models import Devolucion
        data = []
        devoluciones = Devolucion.objects.select_related('cliente', 'producto').all()
        for dev in devoluciones:
            data.append({
                'devolucion_id': dev.id,
                'cliente_id': dev.cliente.id,
                'cliente_nombre': dev.cliente.nombre,
                'producto_id': dev.producto.id,
                'producto_codigo': dev.producto.codigo,
                'producto_nombre': str(dev.producto),
                'tipo': dev.tipo,
                'motivo': dev.motivo,
                'fecha': dev.fecha,
                'estado': dev.estado
            })
        return Response(data)
