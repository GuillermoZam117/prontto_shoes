from rest_framework import serializers
from .models import Inventario, Traspaso

class InventarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventario
        fields = '__all__'

class TraspasoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Traspaso
        fields = '__all__'
