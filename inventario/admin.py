from django.contrib import admin
from .models import Inventario, Traspaso, TraspasoItem

@admin.register(Inventario)
class InventarioAdmin(admin.ModelAdmin):
    list_display = ("tienda", "producto", "cantidad_actual", "fecha_registro", "created_at", "updated_at")
    search_fields = ("producto__codigo", "tienda__nombre")
    list_filter = ("tienda", "producto")

@admin.register(Traspaso)
class TraspasoAdmin(admin.ModelAdmin):
    list_display = ("id", "tienda_origen", "tienda_destino", "fecha", "estado")
    search_fields = ("tienda_origen__nombre", "tienda_destino__nombre")
    list_filter = ("estado", "tienda_origen", "tienda_destino")

@admin.register(TraspasoItem)
class TraspasoItemAdmin(admin.ModelAdmin):
    list_display = ("traspaso", "producto", "cantidad")
    search_fields = ("producto__codigo", "traspaso__tienda_origen__nombre", "traspaso__tienda_destino__nombre")
    list_filter = ("traspaso__estado",)
