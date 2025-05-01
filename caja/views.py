from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Caja, NotaCargo, Factura
from .serializers import CajaSerializer, NotaCargoSerializer, FacturaSerializer

class CajaViewSet(viewsets.ModelViewSet):
    queryset = Caja.objects.all()
    serializer_class = CajaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tienda', 'fecha', 'ingresos', 'egresos', 'saldo_final']

class NotaCargoViewSet(viewsets.ModelViewSet):
    queryset = NotaCargo.objects.all()
    serializer_class = NotaCargoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['caja', 'fecha', 'monto', 'motivo']

class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['pedido', 'folio', 'fecha', 'total']
