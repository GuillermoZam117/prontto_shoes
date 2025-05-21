from rest_framework import serializers
from .models import Pedido, DetallePedido
from productos.models import Producto # Import Producto for validation
from clientes.models import Cliente, DescuentoCliente, ReglaProgramaLealtad # Import Cliente, DescuentoCliente, and ReglaProgramaLealtad
from rest_framework.exceptions import ValidationError
from django.db import transaction
from datetime import date # Import date
from inventario.models import Inventario # Import Inventario model
from caja.models import Caja, TransaccionCaja # Import Caja and TransaccionCaja models
from django.db.models import F # Import F object for atomic updates
from decimal import Decimal # Import Decimal

class DetallePedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetallePedido
        fields = '__all__'
        
class PedidoSerializer(serializers.ModelSerializer):
    detalles = DetallePedidoSerializer(many=True)

    class Meta:
        model = Pedido
        fields = '__all__'
        read_only_fields = ('estado', 'total', 'descuento_aplicado') # estado, total, and descuento_aplicado will be calculated
        
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
            cliente = validated_data.get('cliente') # Get the client from validated data
            tienda = validated_data.get('tienda') # Get the store from validated data
            user = self.context['request'].user # Assuming user is in serializer context
            tipo_pedido = validated_data.get('tipo', 'venta') # Get order type, default to 'venta'

            # Create the Pedido instance without total and discount initially
            pedido = Pedido.objects.create(**validated_data)

            total_pedido = Decimal('0.00')
            for detalle_data in detalles_data:
                producto = detalle_data['producto']
                cantidad = detalle_data['cantidad']
                
                # Basic validation: check if product exists (more complex validation might be needed, e.g., inventory)
                try:
                    producto_instance = Producto.objects.get(id=producto.id)
                except Producto.DoesNotExist:
                    raise ValidationError(f"Producto con ID {producto.id} no encontrado.")                # Check inventory availability before creating order item, only for 'venta' type orders
                inventario_tienda = None  # Initialize to None to avoid 'possibly unbound' error
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
                # Assuming precio_unitario is provided in the details or fetched from product
                # For simplicity, using price from product model; adjust if price comes from input
                precio_unitario = producto_instance.precio # Using product's current price
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
            total_con_descuento = total_pedido # Initialize with total before discount
            if cliente and tipo_pedido == 'venta':
                today = date.today()
                current_month = today.strftime('%Y-%m')
                # Check if payment is received - use the 'pagado' field if included in validated_data
                pago_recibido = validated_data.get('pagado', False)
                
                # Only apply discount if order is paid
                if pago_recibido:
                    try:
                        # Find the applicable discount for the current month
                        descuento_cliente = DescuentoCliente.objects.get(cliente=cliente, mes_vigente=current_month)
                        descuento_aplicado = descuento_cliente.porcentaje
                    except DescuentoCliente.DoesNotExist:
                        # No specific discount for this client this month
                        pass # descuento_aplicado remains 0
                
                pedido.descuento_aplicado = descuento_aplicado
            
                # Calculate final total after discount
                total_con_descuento = total_pedido * (1 - (descuento_aplicado / Decimal('100')))

            pedido.total = total_con_descuento

            # Award loyalty points, only for 'venta' type orders and if a client is linked
            if cliente and tipo_pedido == 'venta':
                try:
                    # Get the active loyalty rule (assuming only one active rule for simplicity)
                    regla_lealtad = ReglaProgramaLealtad.objects.get(activo=True)
                    
                    # Calculate points earned
                    # Ensure monto_compra_requerido is not zero to avoid division by zero
                    if regla_lealtad.monto_compra_requerido > 0:
                        puntos_ganados = int((total_con_descuento / regla_lealtad.monto_compra_requerido) * regla_lealtad.puntos_otorgados)
                        cliente.puntos_lealtad = F('puntos_lealtad') + puntos_ganados
                        cliente.save()
                        self.context['request']._rebuild_authtoken() # To refresh user data if needed

                except ReglaProgramaLealtad.DoesNotExist:
                    # No active loyalty rule found
                    pass # No points are awarded
                except ReglaProgramaLealtad.MultipleObjectsReturned:
                    # Handle case where multiple active rules exist (e.g., log a warning)
                    pass # No points are awarded to be safe

            # Set initial state and save
            # Assuming status is 'surtido' immediately for a sale fulfilled from inventory, 'pendiente' for preventative
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
                    caja=caja_abierta,                    tipo_movimiento='ingreso',
                    monto=total_con_descuento,
                    descripcion=f'Venta Pedido #{pedido.pk}',
                    pedido=pedido, # Link to the sale order
                    created_by=user # Assuming user is the cashier/admin
                )

            return pedido
            
    # You might also need an update method if updating orders is allowed, but often sales are immutable
    # def update(self, instance, validated_data):
    #     raise serializers.ValidationError("Updates to sales orders are not allowed via this endpoint.")
