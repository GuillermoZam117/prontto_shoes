from django.db import models
from clientes.models import Cliente
from tiendas.models import Tienda
from productos.models import Producto
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from django.utils import timezone

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('activo', 'Activo'),
        ('surtido', 'Surtido'),
        ('venta', 'Venta'),
        ('cancelado', 'Cancelado'),
    ]
    TIPO_CHOICES = [
        ('preventivo', 'Preventivo'),
        ('venta', 'Venta'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='pedidos')
    fecha = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    total = models.DecimalField(max_digits=12, decimal_places=2)
    tienda = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='pedidos')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='venta')
    descuento_aplicado = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    pagado = models.BooleanField(default=False)
    
    # Campos para pedidos avanzados
    es_pedido_padre = models.BooleanField(default=False, help_text="Indica si es un pedido padre que puede contener pedidos hijos")
    pedido_padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='pedidos_hijos', help_text="Pedido padre para entregas parciales")
    numero_ticket = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="Número único de ticket para entregas parciales")
    porcentaje_completado = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'), help_text="Porcentaje de completado del pedido")
    fecha_conversion_venta = models.DateTimeField(null=True, blank=True, help_text="Fecha cuando el pedido se convirtió en venta")
    permite_entrega_parcial = models.BooleanField(default=True, help_text="Permite dividir el pedido en entregas parciales")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), related_name='pedidos_creados', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(get_user_model(), related_name='pedidos_actualizados', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"Pedido {self.id} - {self.cliente.nombre}"
    
    @property
    def puede_entrega_parcial(self):
        """Verifica si el pedido puede dividirse en entregas parciales"""
        return (
            self.permite_entrega_parcial and 
            self.estado in ['pendiente', 'activo'] and 
            not self.pedido_padre  # Solo pedidos padre pueden dividirse
        )
    
    @property
    def es_completado(self):
        """Verifica si el pedido está completado"""
        return self.porcentaje_completado >= Decimal('100.00')
    
    @property
    def monto_pendiente(self):
        """Calcula el monto pendiente basado en el porcentaje completado"""
        return self.total * (Decimal('100.00') - self.porcentaje_completado) / Decimal('100.00')
    
    def actualizar_porcentaje_completado(self):
        """Actualiza automáticamente el porcentaje de completado basado en productos entregados"""
        total_productos = self.detalles.aggregate(
            total=models.Sum('cantidad')
        )['total'] or 0
        
        if total_productos == 0:
            self.porcentaje_completado = Decimal('0.00')
        else:
            # Aquí necesitaríamos lógica para calcular productos entregados
            # Por ahora, mantener el valor actual
            pass
        
        self.save(update_fields=['porcentaje_completado'])
    
    def convertir_a_venta(self):
        """Convierte el pedido a venta cuando está completado"""
        if self.es_completado and self.estado != 'venta':
            self.estado = 'venta'
            self.fecha_conversion_venta = timezone.now()
            self.save(update_fields=['estado', 'fecha_conversion_venta'])
    
    def generar_numero_ticket(self):
        """Genera un número de ticket único para entregas parciales"""
        if not self.numero_ticket:
            import uuid
            self.numero_ticket = f"TK-{self.id}-{uuid.uuid4().hex[:8].upper()}"
            self.save(update_fields=['numero_ticket'])
    
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_pedido')
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.producto.codigo} x {self.cantidad} (Pedido {self.pedido.id})"
