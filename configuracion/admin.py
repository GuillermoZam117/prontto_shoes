from django.contrib import admin
from django.utils.html import format_html
from .models import ConfiguracionNegocio, InformacionContacto, DetallesImpresion


class InformacionContactoInline(admin.StackedInline):
    """Inline para información de contacto"""
    model = InformacionContacto
    extra = 0
    
    fieldsets = (
        ('Dirección', {
            'fields': (
                'direccion_linea1', 'direccion_linea2', 
                'ciudad', 'estado_provincia', 
                'codigo_postal', 'pais'
            )
        }),
        ('Contacto', {
            'fields': (
                'telefono_principal', 'telefono_secundario',
                'email_principal', 'email_ventas', 'email_soporte'
            )
        }),
        ('Redes Sociales', {
            'fields': (
                'sitio_web', 'facebook', 'instagram', 
                'twitter', 'whatsapp'
            )
        }),
        ('Horarios', {
            'fields': ('horario_atencion',)
        }),
    )


class DetallesImpresionInline(admin.StackedInline):
    """Inline para detalles de impresión"""
    model = DetallesImpresion
    extra = 0
    
    fieldsets = (
        ('Encabezado', {
            'fields': ('mostrar_logo_impresion', 'texto_encabezado')
        }),
        ('Pie de Página', {
            'fields': ('texto_pie_pagina', 'mensaje_agradecimiento')
        }),
        ('Formato', {
            'fields': (
                'incluir_fecha_hora', 'incluir_numero_ticket',
                'incluir_vendedor', 'incluir_metodo_pago'
            )
        }),
        ('Información Fiscal', {
            'fields': ('rfc', 'regimen_fiscal', 'numero_autorizacion')
        }),
    )


@admin.register(ConfiguracionNegocio)
class ConfiguracionNegocioAdmin(admin.ModelAdmin):
    """Admin para configuración del negocio"""
    
    # Solo permitir editar, no crear/eliminar (Singleton)
    def has_add_permission(self, request):
        return not ConfiguracionNegocio.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    # Campos mostrados en la lista
    list_display = [
        'nombre_negocio', 
        'mostrar_logo', 
        'sidebar_theme', 
        'moneda',
        'updated_at'
    ]
    
    # Campos de solo lectura
    readonly_fields = [
        'created_at', 
        'updated_at', 
        'created_by', 
        'updated_by',
        'mostrar_logo'
    ]
    
    # Inlines
    inlines = [InformacionContactoInline, DetallesImpresionInline]
    
    # Organización de campos
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre_negocio', 'eslogan', 'descripcion')
        }),
        ('Logo y Branding', {
            'fields': ('logo', 'mostrar_logo', 'logo_texto')
        }),
        ('Configuración Visual', {
            'fields': (
                'sidebar_collapsed_default', 'sidebar_theme',
                'color_primario', 'color_secundario'
            )
        }),
        ('Configuración del Sistema', {
            'fields': (
                'moneda', 'simbolo_moneda', 
                'timezone', 'idioma'
            )
        }),
        ('Metadatos', {
            'fields': (
                'created_at', 'updated_at',
                'created_by', 'updated_by'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def mostrar_logo(self, obj):
        """Mostrar preview del logo en el admin"""
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.logo.url
            )
        return "Sin logo"
    mostrar_logo.short_description = "Logo Actual"
    
    def save_model(self, request, obj, form, change):
        """Guardar el modelo con el usuario actual"""
        if change:
            obj.updated_by = request.user
        else:
            obj.created_by = request.user
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        """Asegurar que siempre exista una configuración"""
        qs = super().get_queryset(request)
        if not qs.exists():
            ConfiguracionNegocio.get_configuracion()
        return super().get_queryset(request)


# Personalizar el título del admin
admin.site.site_header = "Administración POS"
admin.site.site_title = "POS Admin"
admin.site.index_title = "Panel de Administración"
