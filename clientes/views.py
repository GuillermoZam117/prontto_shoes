from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Cliente, Anticipo, DescuentoCliente
from .serializers import ClienteSerializer, AnticipoSerializer, DescuentoClienteSerializer
from django_filters.rest_framework import DjangoFilterBackend

# Create your views here.

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['nombre', 'contacto', 'saldo_a_favor', 'tienda']

class AnticipoViewSet(viewsets.ModelViewSet):
    queryset = Anticipo.objects.all()
    serializer_class = AnticipoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'fecha', 'monto']

class DescuentoClienteViewSet(viewsets.ModelViewSet):
    queryset = DescuentoCliente.objects.all()
    serializer_class = DescuentoClienteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente', 'mes_vigente', 'porcentaje']
