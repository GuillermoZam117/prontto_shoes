from decimal import Decimal
from django.db import models
from tiendas.models import Tienda
from django.contrib.auth import get_user_model

class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    contacto = models.CharField(max_length=100, blank=True)
    observaciones = models.TextField(blank=True)
    saldo_a_favor = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    monto_acumulado = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tienda = models.ForeignKey(Tienda, on_delete=models.PROTECT, related_name='clientes')
    user = models.OneToOneField(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='cliente_profile', help_text="Usuario del sistema asociado a este cliente (para login de distribuidoras)")
    max_return_days = models.PositiveIntegerField(default=30)
    puntos_lealtad = models.PositiveIntegerField(default=0)
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
    monto_acumulado_mes_anterior = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), related_name='descuentos_cliente_creados', on_delete=models.SET_NULL, null=True, blank=True)
    updated_by = models.ForeignKey(get_user_model(), related_name='descuentos_cliente_actualizados', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.porcentaje}% - {self.cliente.nombre} ({self.mes_vigente})"

class ReglaProgramaLealtad(models.Model):
    monto_compra_requerido = models.DecimalField(max_digits=12, decimal_places=2, unique=True)
    puntos_otorgados = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Por cada {self.monto_compra_requerido} de compra, otorga {self.puntos_otorgados} puntos"
