from django.contrib import admin
from .models import Devolucion

@admin.register(Devolucion)
class DevolucionAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "producto", "tipo", "motivo", "fecha", "estado", "confirmacion_proveedor", "afecta_inventario", "saldo_a_favor_generado")
    search_fields = ("cliente__nombre", "producto__codigo")
    list_filter = ("tipo", "estado", "confirmacion_proveedor", "afecta_inventario")
# Register your models here.
