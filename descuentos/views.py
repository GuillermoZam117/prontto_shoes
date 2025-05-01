from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import TabuladorDescuento
from .serializers import TabuladorDescuentoSerializer

class TabuladorDescuentoViewSet(viewsets.ModelViewSet):
    queryset = TabuladorDescuento.objects.all()
    serializer_class = TabuladorDescuentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rango_min', 'rango_max', 'porcentaje']

# Create your views here.
