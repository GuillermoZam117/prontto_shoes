from django.contrib import admin
from .models import ColaSincronizacion, ConfiguracionSincronizacion, RegistroSincronizacion
from .security import RegistroAuditoria

@admin.register(ColaSincronizacion)
class ColaSincronizacionAdmin(admin.ModelAdmin):
    list_display = ('tipo_operacion', 'content_type', 'object_id', 'tienda_origen', 'tienda_destino', 'estado', 'fecha_creacion')
    list_filter = ('tipo_operacion', 'estado', 'tienda_origen', 'tiene_conflicto', 'content_type')
    search_fields = ('object_id', 'error_mensaje')
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'intentos')
    actions = ['marcar_pendiente', 'reintentar_sincronizacion']
    
    def marcar_pendiente(self, request, queryset):
        queryset.update(estado='pendiente', intentos=0, error_mensaje=None)
        self.message_user(request, f"Se reiniciaron {queryset.count()} operaciones de sincronización.")
    marcar_pendiente.short_description = "Reiniciar operaciones seleccionadas"
    
    def reintentar_sincronizacion(self, request, queryset):
        from .tasks import procesar_cola_sincronizacion
        for operacion in queryset:
            procesar_cola_sincronizacion(operacion.id)
        self.message_user(request, f"Se han programado {queryset.count()} operaciones para reintento inmediato.")
    reintentar_sincronizacion.short_description = "Reintentar sincronización inmediatamente"

@admin.register(ConfiguracionSincronizacion)
class ConfiguracionSincronizacionAdmin(admin.ModelAdmin):
    list_display = ('tienda', 'sincronizacion_automatica', 'intervalo_minutos', 'ultima_sincronizacion')
    search_fields = ('tienda__nombre',)
    readonly_fields = ('ultima_sincronizacion',)

@admin.register(RegistroSincronizacion)
class RegistroSincronizacionAdmin(admin.ModelAdmin):
    list_display = ('tienda', 'fecha_inicio', 'fecha_fin', 'estado', 'operaciones_totales', 'operaciones_exitosas', 'operaciones_fallidas')
    list_filter = ('estado', 'tienda')
    search_fields = ('tienda__nombre',)
    date_hierarchy = 'fecha_inicio'
    readonly_fields = ('fecha_inicio', 'fecha_fin', 'operaciones_totales', 'operaciones_exitosas', 'operaciones_fallidas', 'operaciones_con_conflicto', 'resumen', 'estado', 'iniciado_por')

@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('accion', 'tienda', 'usuario', 'fecha', 'exitoso')
    list_filter = ('accion', 'tienda', 'exitoso', 'fecha')
    search_fields = ('tienda__nombre', 'usuario__username', 'accion', 'detalles')
    date_hierarchy = 'fecha'
    readonly_fields = ('fecha', 'usuario', 'tienda', 'accion', 'content_type', 'object_id', 'ip_origen', 'detalles', 'exitoso')
