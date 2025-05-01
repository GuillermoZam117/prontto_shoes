from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Inventario, Traspaso
from .serializers import InventarioSerializer, TraspasoSerializer

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
