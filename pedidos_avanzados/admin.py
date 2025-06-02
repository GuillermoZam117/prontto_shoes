from django.contrib import admin
from .models import (
    OrdenCliente, EstadoProductoSeguimiento, EntregaParcial, 
    NotaCredito, PortalClientePolitica, ProductoCompartir
)

@admin.register(OrdenCliente)
class OrdenClienteAdmin(admin.ModelAdmin):
    list_display = ['numero_orden', 'cliente', 'estado', 'fecha_creacion', 'total_productos', 'monto_total']
    list_filter = ['estado', 'fecha_creacion', 'fecha_cierre']
    search_fields = ['numero_orden', 'cliente__nombre', 'cliente__email']
    readonly_fields = ['numero_orden', 'fecha_creacion', 'productos_recibidos']
    fieldsets = (
        ('Información General', {
            'fields': ('numero_orden', 'cliente', 'estado', 'fecha_creacion', 'fecha_cierre')
        }),
        ('Productos y Montos', {
            'fields': ('total_productos', 'productos_recibidos', 'monto_total', 'anticipos_pagados')
        }),
        ('Configuración', {
            'fields': ('observaciones',)
        }),
        ('Auditoría', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(EstadoProductoSeguimiento)
class EstadoProductoSeguimientoAdmin(admin.ModelAdmin):
    list_display = ['detalle_pedido', 'estado_nuevo', 'fecha_cambio', 'usuario_cambio', 'proveedor']
    list_filter = ['estado_nuevo', 'fecha_cambio']
    search_fields = ['detalle_pedido__producto__codigo', 'detalle_pedido__producto__nombre']
    readonly_fields = ['fecha_cambio']

@admin.register(EntregaParcial)
class EntregaParcialAdmin(admin.ModelAdmin):
    list_display = ['ticket_entrega', 'pedido_original', 'fecha_entrega', 'monto_entregado', 'usuario_entrega']
    list_filter = ['fecha_entrega', 'metodo_pago']
    search_fields = ['ticket_entrega', 'pedido_original__id', 'usuario_entrega__username']
    readonly_fields = ['ticket_entrega', 'fecha_entrega']

@admin.register(NotaCredito)
class NotaCreditoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'tipo', 'monto', 'fecha_vencimiento', 'estado']
    list_filter = ['tipo', 'estado', 'created_at', 'fecha_vencimiento']
    search_fields = ['cliente__nombre', 'pedido_origen__id']
    readonly_fields = ['created_at', 'fecha_vencimiento']

@admin.register(PortalClientePolitica)
class PortalClientePoliticaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'activo', 'orden_display']
    list_filter = ['tipo', 'activo']
    search_fields = ['titulo', 'contenido']
    list_editable = ['activo', 'orden_display']

@admin.register(ProductoCompartir)
class ProductoCompartirAdmin(admin.ModelAdmin):
    list_display = ['producto', 'cliente', 'plataforma', 'fecha_compartido', 'clicks_generados']
    list_filter = ['plataforma', 'fecha_compartido']
    search_fields = ['producto__codigo', 'producto__nombre', 'cliente__nombre']
    readonly_fields = ['fecha_compartido', 'clicks_generados']
