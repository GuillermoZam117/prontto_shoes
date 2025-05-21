from rest_framework import serializers
from .models import Devolucion
from productos.models import Producto
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

class DevolucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devolucion
        fields = '__all__'
        
    def validate(self, attrs):
        """
        Validate return requests including supplier returns validation
        """
        producto = attrs.get('producto')
        cliente = attrs.get('cliente')
        detalle_pedido = attrs.get('detalle_pedido')
        
        # Validate days since purchase if a detalle_pedido is provided
        if detalle_pedido:
            # Get the order date
            fecha_pedido = detalle_pedido.pedido.fecha
            fecha_actual = timezone.now()
            dias_transcurridos = (fecha_actual - fecha_pedido).days
            
            # Check if return is within allowed days
            if dias_transcurridos > cliente.max_return_days:
                raise ValidationError({
                    'detalle_pedido': f"Han pasado {dias_transcurridos} días desde la compra. "
                                     f"El límite para devoluciones es de {cliente.max_return_days} días."
                })
        
        # If this is a supplier return (indicated by confirmacion_proveedor=True)
        if attrs.get('confirmacion_proveedor'):
            # Check if product has a default supplier
            if not hasattr(producto, 'proveedor_default') or not producto.proveedor_default:
                raise ValidationError({
                    'confirmacion_proveedor': "No se puede realizar una devolución al proveedor porque "
                                           "el producto no tiene un proveedor predeterminado."
                })
                
            # Check if the product is eligible for supplier returns
            if hasattr(producto, 'permite_devolucion_proveedor') and not producto.permite_devolucion_proveedor:
                raise ValidationError({
                    'confirmacion_proveedor': "Este producto no permite devoluciones al proveedor."
                })
                
            # Validate that there's no ongoing supplier return for this product
            existing_supplier_return = Devolucion.objects.filter(
                producto=producto,
                confirmacion_proveedor=True,
                estado__in=['pendiente', 'validada']  # Only consider ongoing returns
            ).exists()
            
            if existing_supplier_return:
                raise ValidationError({
                    'confirmacion_proveedor': "Ya existe una devolución al proveedor en proceso para este producto."
                })
        
        return attrs
