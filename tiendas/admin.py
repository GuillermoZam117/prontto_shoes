from django.contrib import admin
from .models import Tienda

@admin.register(Tienda)
class TiendaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "direccion", "contacto", "activa", "created_at", "updated_at")
    search_fields = ("nombre", "direccion", "contacto")
    list_filter = ("activa",)
