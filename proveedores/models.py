from django.db import models
from tiendas.models import Tienda
from django.contrib.auth import get_user_model
# from productos.models import Producto # Remove direct import
from requisiciones.models import DetalleRequisicion

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    contacto = models.CharField(max_length=100, blank=True)
    requiere_anticipo = models.BooleanField(default=False)
    max_return_days = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), related_name='proveedores_creados', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(get_user_model(), related_name='proveedores_actualizados', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nombre

class PurchaseOrder(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('recibido', 'Recibido'),
        ('cancelado', 'Cancelado'),
    ]
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='purchase_orders')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    tienda = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='purchase_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), related_name='purchase_orders_creadas', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"PO-{self.id} ({self.proveedor.nombre}) - {self.estado}"

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT, related_name='purchase_order_items') # Use string reference
    cantidad_solicitada = models.PositiveIntegerField()
    cantidad_recibida = models.PositiveIntegerField(default=0)
    detalle_requisicion = models.ForeignKey(DetalleRequisicion, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_order_items')

    def __str__(self):
        return f"{self.producto.codigo} x {self.cantidad_solicitada} (PO-{self.purchase_order.id})"
