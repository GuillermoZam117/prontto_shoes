from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import TabuladorDescuento
from .serializers import TabuladorDescuentoSerializer

class TabuladorDescuentoViewSet(viewsets.ModelViewSet):
    queryset = TabuladorDescuento.objects.all()
    serializer_class = TabuladorDescuentoSerializer
    permission_classes = [IsAuthenticated]

# Create your views here.
