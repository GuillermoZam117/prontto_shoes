from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import TabuladorDescuento
from .serializers import TabuladorDescuentoSerializer
from rest_framework.views import APIView
from rest_framework.response import Response

class TabuladorDescuentoViewSet(viewsets.ModelViewSet):
    queryset = TabuladorDescuento.objects.all()
    serializer_class = TabuladorDescuentoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['rango_min', 'rango_max', 'porcentaje']

class DescuentosReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    """
    Devuelve un reporte del tabulador de descuentos, mostrando rango mínimo, rango máximo y porcentaje.
    """
    def get(self, request):
        from .models import TabuladorDescuento
        data = []
        descuentos = TabuladorDescuento.objects.all()
        for desc in descuentos:
            data.append({
                'id': desc.id,
                'rango_min': desc.rango_min,
                'rango_max': desc.rango_max,
                'porcentaje': desc.porcentaje
            })
        return Response(data)

# Create your views here.
