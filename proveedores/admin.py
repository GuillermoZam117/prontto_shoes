from django.contrib import admin
from .models import Proveedor

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "contacto", "requiere_anticipo", "created_at", "updated_at")
    search_fields = ("nombre", "contacto")
    list_filter = ("requiere_anticipo",)

# Register your models here.
