from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Requisicion, DetalleRequisicion
from .serializers import RequisicionSerializer, DetalleRequisicionSerializer

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
