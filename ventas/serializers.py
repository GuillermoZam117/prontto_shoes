from rest_framework import serializers
from .models import Pedido, DetallePedido
from productos.models import Producto
from clientes.models import Cliente, DescuentoCliente, ReglaProgramaLealtad
from rest_framework.exceptions import ValidationError
from django.db import transaction
from datetime import date
from inventario.models import Inventario
from caja.models import Caja, TransaccionCaja
from django.db.models import F
from decimal import Decimal

class DetallePedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePedido
        fields = '__all__'
        
class PedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoSerializer(many=True)

    class Meta:
        model = Pedido
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')
        
    def validate(self, attrs):
        """
        Validate the order to prevent duplicate orders and implement essential business rules
        """
        cliente = attrs.get('cliente')
        fecha_pedido = attrs.get('fecha')
        tipo_pedido = attrs.get('tipo', 'venta')
        
        # Check for duplicate orders (same client, same day, same type)
        if cliente and fecha_pedido:
            # Extract just the date part for comparison
            fecha_solo_dia = fecha_pedido.date() if hasattr(fecha_pedido, 'date') else fecha_pedido
            
            # Check for existing orders from the same client on the same day with the same type
            existing_orders = Pedido.objects.filter(
                cliente=cliente,
                fecha__date=fecha_solo_dia,
                tipo=tipo_pedido,
                estado__in=['pendiente', 'surtido']  # Only check active orders
            )
            
            if self.instance:  # If this is an update
                existing_orders = existing_orders.exclude(pk=self.instance.pk)
                
            if existing_orders.exists():
                first_order = existing_orders.first()
                if first_order:
                    order_id = first_order.pk
                    raise ValidationError({
                        'cliente': f"Ya existe un pedido del tipo '{tipo_pedido}' para este cliente en esta fecha. "
                                f"Pedido existente: #{order_id}"
                    })
                else:
                    raise ValidationError({
                        'cliente': f"Ya existe un pedido del tipo '{tipo_pedido}' para este cliente en esta fecha."
                    })
        
        # Check for non-returnable products requiring advance payment
        detalles_data = attrs.get('detalles', [])
        pagado = attrs.get('pagado', False)
        
        if tipo_pedido == 'venta' and not pagado:
            for detalle in detalles_data:
                producto = detalle.get('producto')
                if producto and hasattr(producto, 'no_returnable') and producto.no_returnable:
                    raise ValidationError({
                        'pagado': "Este pedido contiene productos no retornables y requiere pago por adelantado."
                    })
                    
        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            detalles_data = validated_data.pop('detalles')
            cliente = validated_data.get('cliente')  # Get the client from validated data
            tienda = validated_data.get('tienda')  # Get the store from validated data
            user = self.context['request'].user  # Assuming user is in serializer context
            tipo_pedido = validated_data.get('tipo', 'venta')  # Get order type, default to 'venta'
            
            # Handle "público en general" when no client is selected
            if not cliente:
                try:
                    # Look for a default "Público en General" client
                    cliente, created = Cliente.objects.get_or_create(
                        nombre='Público en General',
                        defaults={
                            'apellido': '',
                            'telefono': '0000000000',
                            'email': 'publico@general.com',
                            'direccion': 'N/A'
                        }
                    )
                    validated_data['cliente'] = cliente
                except Exception as e:
                    raise ValidationError("Error al crear cliente 'Público en General'")
            
            # Create the Pedido instance without total and discount initially
            pedido = Pedido.objects.create(**validated_data)

            total_pedido = Decimal('0.00')
            for detalle_data in detalles_data:
                producto_id = detalle_data['producto']
                cantidad = detalle_data['cantidad']
                
                # Basic validation: check if product exists
                try:
                    producto_instance = Producto.objects.get(id=producto_id)
                except Producto.DoesNotExist:
                    raise ValidationError(f"Producto con ID {producto_id} no encontrado.")
                
                # Check inventory availability before creating order item, only for 'venta' type orders
                inventario_tienda = None
                if tipo_pedido == 'venta':
                    try:
                        inventario_tienda = Inventario.objects.select_for_update().get(
                            tienda=tienda,
                            producto=producto_instance
                        )
                        if inventario_tienda.cantidad_actual < cantidad:
                            raise ValidationError(f"Cantidad insuficiente en inventario para producto {producto_instance.codigo}. Disponible: {inventario_tienda.cantidad_actual}, Solicitada: {cantidad}")
                    except Inventario.DoesNotExist:
                        raise ValidationError(f"Producto {producto_instance.codigo} no encontrado en el inventario de la tienda {tienda.nombre}.")
                
                # Calculate subtotal and add to total
                precio_unitario = producto_instance.precio
                subtotal = precio_unitario * cantidad
                total_pedido += subtotal
                
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto_instance,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal
                )
                
                # Decrement inventory after creating order item, only for 'venta' type orders
                if tipo_pedido == 'venta' and inventario_tienda is not None:
                    inventario_tienda.cantidad_actual = F('cantidad_actual') - cantidad
                    inventario_tienda.save()
                    
            # Apply discounts based on the client, only for 'venta' type orders and if payment is received
            descuento_aplicado = Decimal('0.00')
            total_con_descuento = total_pedido
            if cliente and tipo_pedido == 'venta' and cliente.nombre != 'Público en General':
                today = date.today()
                current_month = today.strftime('%Y-%m')
                pago_recibido = validated_data.get('pagado', False)
                
                # Only apply discount if order is paid
                if pago_recibido:
                    try:
                        # Find the applicable discount for the current month
                        descuento_cliente = DescuentoCliente.objects.get(cliente=cliente, mes_vigente=current_month)
                        descuento_aplicado = descuento_cliente.porcentaje
                    except DescuentoCliente.DoesNotExist:
                        # No specific discount for this client this month
                        pass
                
                pedido.descuento_aplicado = descuento_aplicado
                # Calculate final total after discount
                total_con_descuento = total_pedido * (1 - (descuento_aplicado / Decimal('100')))

            pedido.total = total_con_descuento

            # Award loyalty points, only for 'venta' type orders and if a client is linked (not public)
            if cliente and tipo_pedido == 'venta' and cliente.nombre != 'Público en General':
                try:
                    # Get the active loyalty rule
                    regla_lealtad = ReglaProgramaLealtad.objects.get(activo=True)
                    
                    # Calculate points earned
                    if regla_lealtad.monto_compra_requerido > 0:
                        puntos_ganados = int((total_con_descuento / regla_lealtad.monto_compra_requerido) * regla_lealtad.puntos_otorgados)
                        cliente.puntos_lealtad = F('puntos_lealtad') + puntos_ganados
                        cliente.save()

                except ReglaProgramaLealtad.DoesNotExist:
                    # No active loyalty rule found
                    pass
                except ReglaProgramaLealtad.MultipleObjectsReturned:
                    # Handle case where multiple active rules exist
                    pass

            # Set initial state and save
            pedido.estado = 'surtido' if tipo_pedido == 'venta' else 'pendiente'
            pedido.save()

            # Record transaction in Caja, only for 'venta' type orders
            if tipo_pedido == 'venta':
                # Find the open cash box for the store and today's date
                today = date.today()
                try:
                    caja_abierta = Caja.objects.select_for_update().get(tienda=tienda, fecha=today, cerrada=False)
                except Caja.DoesNotExist:
                    raise ValidationError(f"No hay una caja abierta para la tienda {tienda.nombre} en la fecha actual para registrar la venta.")
                
                TransaccionCaja.objects.create(
                    caja=caja_abierta,
                    tipo_movimiento='ingreso',
                    monto=total_con_descuento,
                    descripcion=f'Venta Pedido #{pedido.pk}',
                    pedido=pedido,
                    created_by=user
                )

            return pedido
