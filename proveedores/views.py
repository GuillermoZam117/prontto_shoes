from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Proveedor
from .serializers import ProveedorSerializer
from drf_spectacular.utils import extend_schema

# Create your views here.

@extend_schema(tags=["Proveedores"])
class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsAuthenticated]
