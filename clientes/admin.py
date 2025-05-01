from django.contrib import admin
from .models import Cliente, Anticipo, DescuentoCliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "contacto", "saldo_a_favor", "tienda", "created_at", "updated_at")
    search_fields = ("nombre", "contacto")
    list_filter = ("tienda",)

@admin.register(Anticipo)
class AnticipoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "monto", "fecha", "created_at")
    search_fields = ("cliente__nombre",)
    list_filter = ("fecha",)

@admin.register(DescuentoCliente)
class DescuentoClienteAdmin(admin.ModelAdmin):
    list_display = ("cliente", "porcentaje", "mes_vigente", "monto_acumulado_mes_anterior", "created_at")
    search_fields = ("cliente__nombre",)
    list_filter = ("mes_vigente",)
