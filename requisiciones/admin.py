from django.contrib import admin
from .models import Requisicion, DetalleRequisicion

class DetalleRequisicionInline(admin.TabularInline):
    model = DetalleRequisicion
    extra = 0

@admin.register(Requisicion)
class RequisicionAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "fecha", "estado")
    search_fields = ("id", "cliente__nombre")
    list_filter = ("estado",)
    inlines = [DetalleRequisicionInline]

@admin.register(DetalleRequisicion)
class DetalleRequisicionAdmin(admin.ModelAdmin):
    list_display = ("requisicion", "producto", "cantidad")
    search_fields = ("requisicion__id", "producto__codigo")
    list_filter = ("producto",)
