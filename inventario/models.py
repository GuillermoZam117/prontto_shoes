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
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='traspasos')
    tienda_origen = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='traspasos_salida')
    tienda_destino = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='traspasos_entrada')
    cantidad = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=30, default='pendiente')
    created_by = models.ForeignKey(get_user_model(), related_name='traspasos_creados', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.producto.codigo}: {self.tienda_origen.nombre} → {self.tienda_destino.nombre} ({self.cantidad})"
