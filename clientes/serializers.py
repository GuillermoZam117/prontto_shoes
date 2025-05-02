from rest_framework import serializers
from .models import Cliente, Anticipo, DescuentoCliente

class ClienteSerializer(serializers.ModelSerializer):
    """
    Serializador para clientes. Permite alta, consulta y edición de clientes.
    """
    class Meta:
        model = Cliente
        fields = '__all__'
        extra_kwargs = {
            'nombre': {'help_text': 'Nombre completo del cliente'},
            'contacto': {'help_text': 'Persona o medio de contacto'},
            'saldo_a_favor': {'help_text': 'Saldo disponible a favor del cliente'},
            'tienda': {'help_text': 'ID de la tienda asociada'},
        }

class AnticipoSerializer(serializers.ModelSerializer):
    """
    Serializador para anticipos de clientes.
    """
    class Meta:
        model = Anticipo
        fields = '__all__'
        extra_kwargs = {
            'cliente': {'help_text': 'ID del cliente'},
            'monto': {'help_text': 'Monto del anticipo'},
            'fecha': {'help_text': 'Fecha del anticipo (YYYY-MM-DD)'},
        }

class DescuentoClienteSerializer(serializers.ModelSerializer):
    """
    Serializador para descuentos aplicados a clientes.
    """
    class Meta:
        model = DescuentoCliente
        fields = '__all__'
        extra_kwargs = {
            'cliente': {'help_text': 'ID del cliente'},
            'porcentaje': {'help_text': 'Porcentaje de descuento'},
            'mes_vigente': {'help_text': 'Mes de vigencia (YYYY-MM)'},
        }
