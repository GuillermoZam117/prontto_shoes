from rest_framework import serializers
from .models import Cliente, Anticipo, DescuentoCliente

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = '__all__'

class AnticipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anticipo
        fields = '__all__'

class DescuentoClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DescuentoCliente
        fields = '__all__'
