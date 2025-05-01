from rest_framework import serializers
from .models import Pedido, DetallePedido

class DetallePedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePedido
        fields = '__all__'

class PedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    class Meta:
        model = Pedido
        fields = '__all__'
