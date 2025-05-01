from django.contrib import admin
from .models import LogAuditoria

@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "accion", "fecha", "descripcion")
    search_fields = ("usuario__username", "accion", "descripcion")
    list_filter = ("fecha",)

# Register your models here.
