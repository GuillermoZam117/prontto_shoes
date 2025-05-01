from rest_framework import serializers
from .models import Requisicion, DetalleRequisicion

class DetalleRequisicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleRequisicion
        fields = '__all__'

class RequisicionSerializer(serializers.ModelSerializer):
    detalles = DetalleRequisicionSerializer(many=True, read_only=True)
    class Meta:
        model = Requisicion
        fields = '__all__'
