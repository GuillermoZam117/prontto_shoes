from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Requisicion, DetalleRequisicion
from .serializers import RequisicionSerializer, DetalleRequisicionSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Create your views here.

class RequisicionViewSet(viewsets.ModelViewSet):
    queryset = Requisicion.objects.all()
    serializer_class = RequisicionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'fecha', 'estado']

class DetalleRequisicionViewSet(viewsets.ModelViewSet):
    queryset = DetalleRequisicion.objects.all()
    serializer_class = DetalleRequisicionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['requisicion', 'producto', 'cantidad']

class RequisicionesReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Devuelve un reporte de requisiciones realizadas, mostrando cliente, productos, cantidades, estado y fecha.
    """
    def get(self, request):
        from .models import Requisicion
        data = []
        requisiciones = Requisicion.objects.select_related('cliente').prefetch_related('detalles__producto').all()
        for req in requisiciones:
            detalles = []
            for det in req.detalles.all():
                detalles.append({
                    'producto_id': det.producto.id,
                    'producto_codigo': det.producto.codigo,
                    'producto_nombre': str(det.producto),
                    'cantidad': det.cantidad
                })
            data.append({
                'requisicion_id': req.id,
                'cliente_id': req.cliente.id,
                'cliente_nombre': req.cliente.nombre,
                'fecha': req.fecha,
                'estado': req.estado,
                'detalles': detalles
            })
        return Response(data)
