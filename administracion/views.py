from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import LogAuditoria
from .serializers import LogAuditoriaSerializer

# Create your views here.

class LogAuditoriaViewSet(viewsets.ModelViewSet):
    queryset = LogAuditoria.objects.all()
    serializer_class = LogAuditoriaSerializer
    permission_classes = [IsAuthenticated]
