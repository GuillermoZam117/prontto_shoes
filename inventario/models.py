from django.db import models
from tiendas.models import Tienda
from productos.models import Producto
from django.contrib.auth import get_user_model

class Inventario(models.Model):
    tienda = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='inventarios')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='inventarios')
    cantidad_actual = models.IntegerField(default=0)
    fecha_registro = models.DateField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), related_name='inventarios_creados', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(get_user_model(), related_name='inventarios_actualizados', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('tienda', 'producto')

    def __str__(self):
        return f"{self.producto.codigo} - {self.tienda.nombre}: {self.cantidad_actual}"

class Traspaso(models.Model):
    tienda_origen = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='traspasos_salida')
    tienda_destino = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='traspasos_entrada')
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=30, default='pendiente') # Ej: pendiente, enviado, recibido, cancelado
    created_by = models.ForeignKey(get_user_model(), related_name='traspasos_creados', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Traspaso de {self.tienda_origen.nombre} a {self.tienda_destino.nombre} ({self.estado})"

class TraspasoItem(models.Model):
    traspaso = models.ForeignKey(Traspaso, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='traspaso_items')
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.producto.codigo}: {self.cantidad}"
