from django.contrib import admin
from .models import Pedido, DetallePedido

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "fecha", "estado", "total", "tienda", "tipo", "descuento_aplicado", "created_at", "updated_at")
    search_fields = ("id", "cliente__nombre")
    list_filter = ("estado", "tienda", "tipo")
    inlines = [DetallePedidoInline]

@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ("pedido", "producto", "cantidad", "precio_unitario", "subtotal")
    search_fields = ("pedido__id", "producto__codigo")
    list_filter = ("producto",)
