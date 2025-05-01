from django.contrib import admin
from .models import Producto

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "marca", "modelo", "color", "precio", "oferta", "admite_devolucion", "proveedor", "tienda", "created_at", "updated_at")
    search_fields = ("codigo", "marca", "modelo", "color")
    list_filter = ("oferta", "admite_devolucion", "proveedor", "tienda", "temporada")
# Register your models here.
