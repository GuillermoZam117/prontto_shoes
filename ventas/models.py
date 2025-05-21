from django.db import models
from clientes.models import Cliente
from tiendas.models import Tienda
from productos.models import Producto
from django.contrib.auth import get_user_model
from decimal import Decimal

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('surtido', 'Surtido'),
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), related_name='pedidos_creados', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(get_user_model(), related_name='pedidos_actualizados', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Pedido {self.id} - {self.cliente.nombre}"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='detalles_pedido')
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.producto.codigo} x {self.cantidad} (Pedido {self.pedido.id})"
