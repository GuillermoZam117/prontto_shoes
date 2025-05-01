from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Requisicion, DetalleRequisicion
from .serializers import RequisicionSerializer, DetalleRequisicionSerializer

# Create your views here.

class RequisicionViewSet(viewsets.ModelViewSet):
    queryset = Requisicion.objects.all()
    serializer_class = RequisicionSerializer
    permission_classes = [IsAuthenticated]

class DetalleRequisicionViewSet(viewsets.ModelViewSet):
    queryset = DetalleRequisicion.objects.all()
    serializer_class = DetalleRequisicionSerializer
    permission_classes = [IsAuthenticated]
