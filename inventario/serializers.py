from rest_framework import serializers
from .models import Inventario, Traspaso, TraspasoItem
from productos.serializers import ProductoSerializer # Assuming ProductoSerializer exists in productos app
from productos.models import Producto  # Importaci�n de Producto
from tiendas.serializers import TiendaSerializer # Assuming TiendaSerializer exists in tiendas app
from django.db import transaction
from django.db.models import F

class InventarioSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    tienda = TiendaSerializer(read_only=True)

    class Meta:
        model = Inventario
        fields = "__all__"

class TraspasoItemSerializer(serializers.ModelSerializer):
    producto_detail = ProductoSerializer(source="producto", read_only=True)

    class Meta:
        model = TraspasoItem
        fields = ["id", "producto", "cantidad", "producto_detail"]
        extra_kwargs = {
            "producto": {"write_only": True}
        }

class TraspasoSerializer(serializers.ModelSerializer):
    items = TraspasoItemSerializer(many=True)
    tienda_origen_detail = TiendaSerializer(source="tienda_origen", read_only=True)
    tienda_destino_detail = TiendaSerializer(source="tienda_destino", read_only=True)

    class Meta:
        model = Traspaso
        fields = ["id", "tienda_origen", "tienda_destino", "fecha", "estado", "created_by", "items", "tienda_origen_detail", "tienda_destino_detail"]
        read_only_fields = ["estado", "created_by"]
        extra_kwargs = {
            "tienda_origen": {"write_only": True},
            "tienda_destino": {"write_only": True},
        }
        
    def create(self, validated_data):
        # Extract items data and validate inventory in source store
        items_data = validated_data.pop("items")
        tienda_origen = validated_data["tienda_origen"]
        tienda_destino = validated_data["tienda_destino"]
        
        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Create the transfer
            traspaso = Traspaso.objects.create(**validated_data)
            
            # Process all items and update inventory
            for item_data in items_data:
                producto = item_data["producto"]
                cantidad = item_data["cantidad"]
                
                # Create transfer item
                TraspasoItem.objects.create(traspaso=traspaso, **item_data)
                
                # Update inventory tracking: decrease from source store, increase in destination store
                try:
                    # Update source inventory (decrease)
                    inventario_origen = Inventario.objects.select_for_update().get(
                        tienda=tienda_origen, 
                        producto=producto
                    )
                    
                    # Validate sufficient inventory in source store
                    if inventario_origen.cantidad_actual < cantidad:
                        raise serializers.ValidationError(
                            f"Cantidad insuficiente en tienda de origen para el producto {producto.codigo}. "
                            f"Disponible: {inventario_origen.cantidad_actual}, Solicitada: {cantidad}"
                        )
                        
                    # Update destination inventory (increase)
                    inventario_destino, created = Inventario.objects.select_for_update().get_or_create(
                        tienda=tienda_destino,
                        producto=producto,
                        defaults={'cantidad_actual': 0}
                    )
                    
                    # Perform the inventory updates using F expressions for atomicity
                    inventario_origen.cantidad_actual = F('cantidad_actual') - cantidad
                    inventario_destino.cantidad_actual = F('cantidad_actual') + cantidad
                    
                    # Save the updated inventories
                    inventario_origen.save()
                    inventario_destino.save()
                    
                except Inventario.DoesNotExist:
                    raise serializers.ValidationError(
                        f"No existe inventario del producto {producto.codigo} en la tienda de origen."
                    )
                
            # Mark transfer as completed
            traspaso.estado = "completado"
            traspaso.save()
            
            return traspaso

class ProductoInventarioSerializer(serializers.ModelSerializer):
    inventario = InventarioSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = ["id", "codigo", "marca", "modelo", "color", "propiedad", "inventario"]
