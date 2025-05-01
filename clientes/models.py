from django.db import models
from tiendas.models import Tienda
from django.contrib.auth import get_user_model

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    contacto = models.CharField(max_length=100, blank=True)
    observaciones = models.TextField(blank=True)
    saldo_a_favor = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tienda = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='clientes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), related_name='clientes_creados', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(get_user_model(), related_name='clientes_actualizados', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nombre

class Anticipo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='anticipos')
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(get_user_model(), related_name='anticipos_creados', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Anticipo {self.monto} - {self.cliente.nombre}"

class DescuentoCliente(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='descuentos')
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    mes_vigente = models.CharField(max_length=7)  # Formato YYYY-MM
    monto_acumulado_mes_anterior = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.porcentaje}% - {self.cliente.nombre} ({self.mes_vigente})"
