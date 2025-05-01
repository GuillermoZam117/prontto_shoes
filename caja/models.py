from django.db import models
from tiendas.models import Tienda
from ventas.models import Pedido
from django.contrib.auth import get_user_model

class Caja(models.Model):
    tienda = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='cajas')
    fecha = models.DateField()
    ingresos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    egresos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo_final = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), related_name='cajas_creadas', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(get_user_model(), related_name='cajas_actualizadas', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Caja {self.tienda.nombre} - {self.fecha}"

class NotaCargo(models.Model):
    caja = models.ForeignKey(Caja, on_delete=models.CASCADE, related_name='notas_cargo')
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    motivo = models.CharField(max_length=255)
    fecha = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(get_user_model(), related_name='notas_cargo_creadas', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Nota de cargo {self.monto} - {self.caja.tienda.nombre}"

class Factura(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.PROTECT, related_name='factura')
    folio = models.CharField(max_length=50, unique=True)
    fecha = models.DateField()
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(get_user_model(), related_name='facturas_creadas', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Factura {self.folio} - Pedido {self.pedido.id}"
