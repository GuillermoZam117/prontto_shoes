from rest_framework import serializers
from .models import Inventario, Traspaso, TraspasoItem
from productos.serializers import ProductoSerializer # Assuming ProductoSerializer exists in productos app
from productos.models import Producto  # Importación de Producto
from tiendas.serializers import TiendaSerializer # Assuming TiendaSerializer exists in tiendas app

class InventarioSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    tienda = TiendaSerializer(read_only=True)

    class Meta:
        model = Inventario
        fields = '__all__'

class TraspasoItemSerializer(serializers.ModelSerializer):
    producto_detail = ProductoSerializer(source='producto', read_only=True)

    class Meta:
        model = TraspasoItem
        fields = ['id', 'producto', 'cantidad', 'producto_detail']
        extra_kwargs = {
            'producto': {'write_only': True}
        }

class TraspasoSerializer(serializers.ModelSerializer):
    items = TraspasoItemSerializer(many=True)
    tienda_origen_detail = TiendaSerializer(source='tienda_origen', read_only=True)
    tienda_destino_detail = TiendaSerializer(source='tienda_destino', read_only=True)

    class Meta:
        model = Traspaso
        fields = ['id', 'tienda_origen', 'tienda_destino', 'fecha', 'estado', 'created_by', 'items', 'tienda_origen_detail', 'tienda_destino_detail']
        read_only_fields = ['estado', 'created_by']
        extra_kwargs = {
            'tienda_origen': {'write_only': True},
            'tienda_destino': {'write_only': True},
        }

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        traspaso = Traspaso.objects.create(**validated_data)
        for item_data in items_data:
            TraspasoItem.objects.create(traspaso=traspaso, **item_data)
        return traspaso

class ProductoInventarioSerializer(serializers.ModelSerializer):
    inventario = InventarioSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = ['id', 'codigo', 'marca', 'modelo', 'color', 'propiedad', 'inventario']
