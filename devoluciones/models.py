from django.db import models
from clientes.models import Cliente
from productos.models import Producto
from django.contrib.auth import get_user_model

class Devolucion(models.Model):
    TIPO_CHOICES = [
        ('defecto', 'Defecto'),
        ('cambio', 'Cambio'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('validada', 'Validada'),
        ('rechazada', 'Rechazada'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='devoluciones')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='devoluciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    motivo = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    confirmacion_proveedor = models.BooleanField(default=False)
    afecta_inventario = models.BooleanField(default=True)
    saldo_a_favor_generado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_by = models.ForeignKey(get_user_model(), related_name='devoluciones_creadas', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Devolución {self.id} - {self.cliente.nombre} - {self.producto.codigo}"
