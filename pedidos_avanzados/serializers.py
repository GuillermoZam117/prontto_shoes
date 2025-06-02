"""
Serializers para el sistema de pedidos avanzados
Sistema POS Pronto Shoes
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    OrdenCliente, EstadoProductoSeguimiento, EntregaParcial,
    NotaCredito, PortalClientePolitica, ProductoCompartir
)
from ventas.models import Pedido, DetallePedido
from clientes.models import Cliente
from productos.models import Producto

User = get_user_model()


class OrdenClienteSerializer(serializers.ModelSerializer):
    """Serializer para OrdenCliente"""
    
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    porcentaje_completado = serializers.ReadOnlyField()
    esta_completa = serializers.ReadOnlyField()
    productos_pendientes = serializers.SerializerMethodField()
    
    class Meta:
        model = OrdenCliente
        fields = [
            'id', 'numero_orden', 'cliente', 'cliente_nombre', 'estado',
            'fecha_creacion', 'fecha_cierre', 'total_productos', 
            'productos_recibidos', 'monto_total', 'anticipos_pagados',
            'porcentaje_completado', 'esta_completa', 'productos_pendientes',
            'observaciones', 'created_at', 'updated_at'
        ]
        read_only_fields = ['numero_orden', 'fecha_creacion', 'created_at', 'updated_at']
    
    def get_productos_pendientes(self, obj):
        """Calcula productos pendientes de recibir"""
        return obj.total_productos - obj.productos_recibidos
    
    def create(self, validated_data):
        """Override create para generar número de orden automático"""
        from django.utils import timezone
        
        if not validated_data.get('numero_orden'):
            cliente_id = validated_data['cliente'].id
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            validated_data['numero_orden'] = f"ORD-{timestamp}-{cliente_id}"
        
        return super().create(validated_data)


class OrdenClienteListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de órdenes"""
    
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    porcentaje_completado = serializers.ReadOnlyField()
    
    class Meta:
        model = OrdenCliente
        fields = [
            'id', 'numero_orden', 'cliente_nombre', 'estado',
            'fecha_creacion', 'total_productos', 'monto_total',
            'porcentaje_completado'
        ]


class EstadoProductoSeguimientoSerializer(serializers.ModelSerializer):
    """Serializer para seguimiento de productos"""
    
    producto_codigo = serializers.CharField(source='detalle_pedido.producto.codigo', read_only=True)
    producto_nombre = serializers.CharField(source='detalle_pedido.producto.nombre', read_only=True)
    pedido_id = serializers.IntegerField(source='detalle_pedido.pedido.id', read_only=True)
    usuario_cambio_nombre = serializers.CharField(source='usuario_cambio.get_full_name', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    
    class Meta:
        model = EstadoProductoSeguimiento
        fields = [
            'id', 'detalle_pedido', 'producto_codigo', 'producto_nombre',
            'pedido_id', 'estado_anterior', 'estado_nuevo', 'fecha_cambio',
            'usuario_cambio', 'usuario_cambio_nombre', 'observaciones',
            'ubicacion', 'proveedor', 'proveedor_nombre'
        ]
        read_only_fields = ['fecha_cambio']
    
    def create(self, validated_data):
        """Override create para establecer estado anterior automáticamente"""
        detalle_pedido = validated_data['detalle_pedido']
        
        # Buscar último estado del producto
        ultimo_seguimiento = EstadoProductoSeguimiento.objects.filter(
            detalle_pedido=detalle_pedido
        ).order_by('-fecha_cambio').first()
        
        if ultimo_seguimiento:
            validated_data['estado_anterior'] = ultimo_seguimiento.estado_nuevo
        
        return super().create(validated_data)


class EntregaParcialSerializer(serializers.ModelSerializer):
    """Serializer para entregas parciales"""
    
    pedido_original_numero = serializers.CharField(source='pedido_original.id', read_only=True)
    pedido_nuevo_numero = serializers.CharField(source='pedido_nuevo.id', read_only=True)
    usuario_entrega_nombre = serializers.CharField(source='usuario_entrega.get_full_name', read_only=True)
    productos_info = serializers.SerializerMethodField()
    
    class Meta:
        model = EntregaParcial
        fields = [
            'id', 'pedido_original', 'pedido_original_numero',
            'pedido_nuevo', 'pedido_nuevo_numero', 'ticket_entrega',
            'fecha_entrega', 'productos_entregados', 'productos_info',
            'monto_entregado', 'metodo_pago', 'usuario_entrega',
            'usuario_entrega_nombre', 'observaciones'
        ]
        read_only_fields = ['ticket_entrega', 'fecha_entrega']
    
    def get_productos_info(self, obj):
        """Formatea información de productos entregados"""
        if not obj.productos_entregados:
            return []
        
        productos_info = []
        for item in obj.productos_entregados:
            productos_info.append({
                'codigo': item.get('codigo', ''),
                'cantidad': item.get('cantidad', 0),
                'precio_unitario': item.get('precio_unitario', 0),
                'subtotal': item.get('subtotal', 0)
            })
        
        return productos_info
    
    def create(self, validated_data):
        """Override create para generar ticket automático"""
        from django.utils import timezone
        import uuid
        
        if not validated_data.get('ticket_entrega'):
            pedido_id = validated_data['pedido_original'].id
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            unique_id = uuid.uuid4().hex[:6].upper()
            validated_data['ticket_entrega'] = f"EP-{pedido_id}-{timestamp}-{unique_id}"
        
        return super().create(validated_data)


class NotaCreditoSerializer(serializers.ModelSerializer):
    """Serializer para notas de crédito"""
    
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    pedido_origen_numero = serializers.IntegerField(source='pedido_origen.id', read_only=True)
    aplicada_en_pedido_numero = serializers.IntegerField(source='aplicada_en_pedido.id', read_only=True)
    esta_vencida = serializers.ReadOnlyField()
    dias_para_vencimiento = serializers.SerializerMethodField()
    created_by_nombre = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = NotaCredito
        fields = [
            'id', 'cliente', 'cliente_nombre', 'tipo', 'monto', 'motivo',
            'pedido_origen', 'pedido_origen_numero', 'aplicada_en_pedido',
            'aplicada_en_pedido_numero', 'fecha_vencimiento', 'estado',
            'fecha_aplicacion', 'esta_vencida', 'dias_para_vencimiento',
            'created_by', 'created_by_nombre', 'created_at'
        ]
        read_only_fields = ['fecha_vencimiento', 'created_at']
    
    def get_dias_para_vencimiento(self, obj):
        """Calcula días restantes para vencimiento"""
        if obj.estado != 'ACTIVA':
            return 0
        
        from django.utils import timezone
        dias = (obj.fecha_vencimiento - timezone.now().date()).days
        return max(0, dias)


class PortalClientePoliticaSerializer(serializers.ModelSerializer):
    """Serializer para políticas del portal de cliente"""
    
    class Meta:
        model = PortalClientePolitica
        fields = [
            'id', 'titulo', 'contenido', 'tipo', 'activo',
            'orden_display', 'fecha_vigencia', 'created_at', 'updated_at'
        ]


class ProductoCompartirSerializer(serializers.ModelSerializer):
    """Serializer para productos compartidos"""
    
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.nombre', read_only=True)
    
    class Meta:
        model = ProductoCompartir
        fields = [
            'id', 'producto', 'producto_codigo', 'producto_nombre',
            'cliente', 'cliente_nombre', 'plataforma', 'url_compartida',
            'fecha_compartido', 'clicks_generados'
        ]
        read_only_fields = ['fecha_compartido', 'clicks_generados']


# Serializers para operaciones específicas

class CrearOrdenDesdepedidosSerializer(serializers.Serializer):
    """Serializer para crear orden desde múltiples pedidos"""
    
    cliente_id = serializers.IntegerField()
    pedidos_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    observaciones = serializers.CharField(required=False, allow_blank=True)
    
    def validate_cliente_id(self, value):
        """Valida que el cliente exista"""
        try:
            Cliente.objects.get(id=value)
        except Cliente.DoesNotExist:
            raise serializers.ValidationError("Cliente no encontrado")
        return value
    
    def validate_pedidos_ids(self, value):
        """Valida que los pedidos existan y sean válidos"""
        pedidos = Pedido.objects.filter(id__in=value)
        
        if pedidos.count() != len(value):
            raise serializers.ValidationError("Algunos pedidos no existen")
        
        # Validar que todos los pedidos sean del mismo cliente
        clientes = pedidos.values_list('cliente_id', flat=True).distinct()
        if len(clientes) > 1:
            raise serializers.ValidationError("Todos los pedidos deben ser del mismo cliente")
        
        # Validar estados válidos
        estados_invalidos = pedidos.exclude(estado='pendiente')
        if estados_invalidos.exists():
            raise serializers.ValidationError("Solo se pueden consolidar pedidos en estado 'pendiente'")
        
        return value


class ProcesarEntregaParcialSerializer(serializers.Serializer):
    """Serializer para procesar entrega parcial"""
    
    pedido_id = serializers.IntegerField()
    productos_entregar = serializers.ListField(
        child=serializers.DictField()
    )
    observaciones = serializers.CharField(required=False, allow_blank=True)
    metodo_pago = serializers.CharField(required=False, allow_blank=True)
    
    def validate_pedido_id(self, value):
        """Valida que el pedido exista y permita entregas parciales"""
        try:
            pedido = Pedido.objects.get(id=value)
            if not pedido.puede_entrega_parcial:
                raise serializers.ValidationError("Este pedido no permite entregas parciales")
        except Pedido.DoesNotExist:
            raise serializers.ValidationError("Pedido no encontrado")
        return value
    
    def validate_productos_entregar(self, value):
        """Valida la estructura de productos a entregar"""
        for item in value:
            if 'detalle_id' not in item or 'cantidad_entregar' not in item:
                raise serializers.ValidationError(
                    "Cada producto debe tener 'detalle_id' y 'cantidad_entregar'"
                )
            
            if item['cantidad_entregar'] <= 0:
                raise serializers.ValidationError("La cantidad a entregar debe ser mayor a 0")
        
        return value


class AplicarCreditoSerializer(serializers.Serializer):
    """Serializer para aplicar crédito a un pedido"""
    
    cliente_id = serializers.IntegerField()
    pedido_id = serializers.IntegerField()
    monto_aplicar = serializers.DecimalField(
        max_digits=12, decimal_places=2, 
        required=False, allow_null=True
    )
    
    def validate_cliente_id(self, value):
        """Valida que el cliente exista"""
        try:
            Cliente.objects.get(id=value)
        except Cliente.DoesNotExist:
            raise serializers.ValidationError("Cliente no encontrado")
        return value
    
    def validate_pedido_id(self, value):
        """Valida que el pedido exista"""
        try:
            Pedido.objects.get(id=value)
        except Pedido.DoesNotExist:
            raise serializers.ValidationError("Pedido no encontrado")
        return value
    
    def validate(self, attrs):
        """Validación cruzada"""
        cliente_id = attrs['cliente_id']
        pedido_id = attrs['pedido_id']
        
        # Verificar que el pedido pertenezca al cliente
        try:
            pedido = Pedido.objects.get(id=pedido_id, cliente_id=cliente_id)
        except Pedido.DoesNotExist:
            raise serializers.ValidationError("El pedido no pertenece al cliente especificado")
        
        # Verificar que el cliente tenga crédito disponible
        credito_disponible = NotaCredito.objects.filter(
            cliente_id=cliente_id,
            tipo='CREDITO',
            estado='ACTIVA'
        ).aggregate(
            total=serializers.models.Sum('monto')
        )['total'] or 0
        
        if credito_disponible == 0:
            raise serializers.ValidationError("El cliente no tiene crédito disponible")
        
        # Validar monto si se especificó
        monto_aplicar = attrs.get('monto_aplicar')
        if monto_aplicar and monto_aplicar > credito_disponible:
            raise serializers.ValidationError(
                f"Monto a aplicar ({monto_aplicar}) excede el crédito disponible ({credito_disponible})"
            )
        
        attrs['pedido'] = pedido
        attrs['credito_disponible'] = credito_disponible
        return attrs


class RegistrarCompartidoSerializer(serializers.Serializer):
    """Serializer para registrar producto compartido"""
    
    producto_id = serializers.IntegerField()
    cliente_id = serializers.IntegerField()
    plataforma = serializers.ChoiceField(choices=ProductoCompartir.PLATAFORMA_CHOICES)
    url_compartida = serializers.URLField(required=False, allow_blank=True)
    
    def validate_producto_id(self, value):
        """Valida que el producto exista"""
        try:
            Producto.objects.get(id=value)
        except Producto.DoesNotExist:
            raise serializers.ValidationError("Producto no encontrado")
        return value
    
    def validate_cliente_id(self, value):
        """Valida que el cliente exista"""
        try:
            Cliente.objects.get(id=value)
        except Cliente.DoesNotExist:
            raise serializers.ValidationError("Cliente no encontrado")
        return value
