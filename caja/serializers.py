from rest_framework import serializers
from .models import Caja, NotaCargo, Factura, TransaccionCaja

class CajaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Caja
        fields = '__all__'

class NotaCargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotaCargo
        fields = '__all__'

class FacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = '__all__'

class TransaccionCajaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransaccionCaja
        fields = '__all__'
