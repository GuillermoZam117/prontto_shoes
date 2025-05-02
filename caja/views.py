from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Caja, NotaCargo, Factura
from .serializers import CajaSerializer, NotaCargoSerializer, FacturaSerializer
from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model

@extend_schema(tags=["Caja"])
class CajaViewSet(viewsets.ModelViewSet):
    queryset = Caja.objects.all()
    serializer_class = CajaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tienda', 'fecha', 'ingresos', 'egresos', 'saldo_final']

@extend_schema(tags=["Caja"])
class NotaCargoViewSet(viewsets.ModelViewSet):
    queryset = NotaCargo.objects.all()
    serializer_class = NotaCargoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['caja', 'fecha', 'monto', 'motivo']

@extend_schema(tags=["Caja"])
class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['pedido', 'folio', 'fecha', 'total']

class MovimientosCajaReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Devuelve un reporte de movimientos de caja agrupados por tienda y fecha.
    """
    def get(self, request):
        data = []
        from .models import Caja, NotaCargo
        cajas = Caja.objects.select_related('tienda', 'created_by').all()
        for caja in cajas:
            movimientos = []
            # Ingresos y egresos globales de la caja
            movimientos.append({
                'tipo': 'ingresos',
                'monto': caja.ingresos,
                'usuario': caja.created_by.username if caja.created_by else None,
                'observaciones': 'Ingresos totales del día'
            })
            movimientos.append({
                'tipo': 'egresos',
                'monto': caja.egresos,
                'usuario': caja.created_by.username if caja.created_by else None,
                'observaciones': 'Egresos totales del día'
            })
            # Notas de cargo asociadas a la caja
            notas = NotaCargo.objects.filter(caja=caja).select_related('created_by')
            for nota in notas:
                movimientos.append({
                    'tipo': 'nota_cargo',
                    'monto': nota.monto,
                    'usuario': nota.created_by.username if nota.created_by else None,
                    'observaciones': nota.motivo
                })
            data.append({
                'tienda_id': caja.tienda.id,
                'tienda_nombre': caja.tienda.nombre,
                'fecha': caja.fecha,
                'saldo_final': caja.saldo_final,
                'movimientos': movimientos
            })
        return Response(data)
