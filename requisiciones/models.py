from django.db import models
from clientes.models import Cliente
# from productos.models import Producto # Remove direct import
from django.contrib.auth import get_user_model

class Requisicion(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('procesada', 'Procesada'),
        ('cancelada', 'Cancelada'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='requisiciones')
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    created_by = models.ForeignKey(get_user_model(), related_name='requisiciones_creadas', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Requisición {self.id} - {self.cliente.nombre}"

class DetalleRequisicion(models.Model):
    requisicion = models.ForeignKey(Requisicion, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('productos.Producto', on_delete=models.PROTECT, related_name='detalles_requisicion') # Use string reference
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.producto.codigo} x {self.cantidad} (Requisición {self.requisicion.id})"
