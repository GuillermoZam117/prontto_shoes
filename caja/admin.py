from django.contrib import admin
from .models import Caja, NotaCargo, Factura

@admin.register(Caja)
class CajaAdmin(admin.ModelAdmin):
    list_display = ("tienda", "fecha", "ingresos", "egresos", "saldo_final", "created_at", "updated_at")
    search_fields = ("tienda__nombre",)
    list_filter = ("tienda", "fecha")

@admin.register(NotaCargo)
class NotaCargoAdmin(admin.ModelAdmin):
    list_display = ("caja", "monto", "motivo", "fecha", "created_at")
    search_fields = ("caja__tienda__nombre", "motivo")
    list_filter = ("fecha",)

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ("pedido", "folio", "fecha", "total", "created_at")
    search_fields = ("folio", "pedido__id")
    list_filter = ("fecha",)
# Register your models here.
