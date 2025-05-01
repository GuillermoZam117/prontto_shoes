from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Inventario, Traspaso
from .serializers import InventarioSerializer, TraspasoSerializer

# Create your views here.

class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer
    permission_classes = [IsAuthenticated]

class TraspasoViewSet(viewsets.ModelViewSet):
    queryset = Traspaso.objects.all()
    serializer_class = TraspasoSerializer
    permission_classes = [IsAuthenticated]
