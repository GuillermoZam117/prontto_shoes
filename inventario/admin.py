from django.contrib import admin
from .models import Inventario, Traspaso

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ("tienda", "producto", "cantidad_actual", "fecha_registro", "created_at", "updated_at")
    search_fields = ("producto__codigo", "tienda__nombre")
    list_filter = ("tienda", "producto")

@admin.register(Traspaso)
class TraspasoAdmin(admin.ModelAdmin):
    list_display = ("producto", "tienda_origen", "tienda_destino", "cantidad", "fecha", "estado")
    search_fields = ("producto__codigo", "tienda_origen__nombre", "tienda_destino__nombre")
    list_filter = ("estado", "tienda_origen", "tienda_destino")
