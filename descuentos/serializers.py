from rest_framework import serializers
from .models import TabuladorDescuento

class TabuladorDescuentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TabuladorDescuento
        fields = '__all__'
