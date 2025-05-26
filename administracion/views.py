from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import LogAuditoria
from .serializers import LogAuditoriaSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Create your views here.

class LogAuditoriaViewSet(viewsets.ModelViewSet):
    queryset = LogAuditoria.objects.all()
    serializer_class = LogAuditoriaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['usuario', 'accion', 'fecha']

class LogsAuditoriaReporteAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogAuditoriaSerializer  # Add this for DRF Spectacular
    """
    Devuelve un reporte de logs de auditoría, mostrando usuario, acción, fecha y descripción.
    """
    def get(self, request):
        from .models import LogAuditoria
        data = []
        logs = LogAuditoria.objects.select_related('usuario').all().order_by('-fecha')
        for log in logs:
            data.append({
                'id': log.id,
                'usuario_id': log.usuario.id if log.usuario else None,
                'usuario_username': log.usuario.username if log.usuario else None,
                'accion': log.accion,
                'fecha': log.fecha,
                'descripcion': log.descripcion
            })
        return Response(data)
