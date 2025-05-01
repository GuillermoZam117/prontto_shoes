from django.contrib import admin
from .models import TabuladorDescuento

@admin.register(TabuladorDescuento)
class TabuladorDescuentoAdmin(admin.ModelAdmin):
    list_display = ("rango_min", "rango_max", "porcentaje")
    search_fields = ("rango_min", "rango_max")
    list_filter = ("porcentaje",)
# Register your models here.
