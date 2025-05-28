from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import os


def logo_upload_path(instance, filename):
    """Define el path para subir los logos"""
    ext = filename.split('.')[-1]
    return f'logos/logo.{ext}'


class ConfiguracionNegocio(models.Model):
    """
    Modelo para la configuración general del negocio
    Singleton pattern - solo debe existir un registro
    """
    # Información básica del negocio
    nombre_negocio = models.CharField(max_length=200, default="Mi Negocio")
    eslogan = models.CharField(max_length=300, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    
    # Logo y branding
    logo = models.ImageField(
        upload_to=logo_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg'])],
        help_text="Logo del negocio (JPG, PNG, SVG - máximo 2MB)"
    )
    logo_texto = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Texto alternativo cuando no hay logo"
    )
    
    # Configuración visual del sidebar
    sidebar_collapsed_default = models.BooleanField(
        default=False,
        help_text="Estado por defecto del sidebar (expandido/colapsado)"
    )
    sidebar_theme = models.CharField(
        max_length=20,
        choices=[
            ('light', 'Claro'),
            ('dark', 'Oscuro'),
            ('primary', 'Color Primario'),
        ],
        default='dark'
    )
    
    # Colores personalizados
    color_primario = models.CharField(
        max_length=7,
        default="#007bff",
        help_text="Color primario en formato hexadecimal (#000000)"
    )
    color_secundario = models.CharField(
        max_length=7,
        default="#6c757d",
        help_text="Color secundario en formato hexadecimal (#000000)"
    )
    
    # Configuración del sistema
    moneda = models.CharField(max_length=10, default="USD")
    simbolo_moneda = models.CharField(max_length=5, default="$")
    timezone = models.CharField(max_length=50, default="UTC")
    idioma = models.CharField(
        max_length=10,
        choices=[
            ('es', 'Español'),
            ('en', 'English'),
        ],
        default='es'
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='configuracion_creada'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='configuracion_actualizada'
    )
    
    class Meta:
        verbose_name = "Configuración del Negocio"
        verbose_name_plural = "Configuraciones del Negocio"
        db_table = 'configuracion_negocio'
    
    def __str__(self):
        return f"Configuración: {self.nombre_negocio}"
    
    def save(self, *args, **kwargs):
        """Asegurar que solo exista una configuración (Singleton)"""
        if not self.pk and ConfiguracionNegocio.objects.exists():
            # Si no tiene PK y ya existe una configuración, actualizar la existente
            existing = ConfiguracionNegocio.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)
    
    @classmethod
    def get_configuracion(cls):
        """Obtener o crear la configuración del negocio"""
        config, created = cls.objects.get_or_create(
            defaults={
                'nombre_negocio': 'Mi Negocio',
                'logo_texto': 'Mi Negocio',
            }
        )
        return config
    
    def delete(self, *args, **kwargs):
        """Prevenir eliminación de la configuración"""
        # No permitir eliminar la configuración, solo resetear valores
        self.nombre_negocio = "Mi Negocio"
        self.logo_texto = "Mi Negocio"
        if self.logo:
            self.logo.delete(save=False)
            self.logo = None
        self.save()


class InformacionContacto(models.Model):
    """Información de contacto del negocio"""
    configuracion = models.OneToOneField(
        ConfiguracionNegocio,
        on_delete=models.CASCADE,
        related_name='contacto'
    )
    
    # Dirección
    direccion_linea1 = models.CharField(max_length=200, blank=True, null=True)
    direccion_linea2 = models.CharField(max_length=200, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    estado_provincia = models.CharField(max_length=100, blank=True, null=True)
    codigo_postal = models.CharField(max_length=20, blank=True, null=True)
    pais = models.CharField(max_length=100, default="México")
    
    # Contacto
    telefono_principal = models.CharField(max_length=20, blank=True, null=True)
    telefono_secundario = models.CharField(max_length=20, blank=True, null=True)
    email_principal = models.EmailField(blank=True, null=True)
    email_ventas = models.EmailField(blank=True, null=True)
    email_soporte = models.EmailField(blank=True, null=True)
    
    # Redes sociales
    sitio_web = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    
    # Horarios
    horario_atencion = models.TextField(
        blank=True,
        null=True,
        help_text="Horarios de atención al cliente"
    )
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Información de Contacto"
        verbose_name_plural = "Información de Contacto"
        db_table = 'configuracion_contacto'
    
    def __str__(self):
        return f"Contacto: {self.configuracion.nombre_negocio}"


class DetallesImpresion(models.Model):
    """Configuración para detalles de impresión en recibos y facturas"""
    configuracion = models.OneToOneField(
        ConfiguracionNegocio,
        on_delete=models.CASCADE,
        related_name='impresion'
    )
    
    # Encabezado de impresión
    mostrar_logo_impresion = models.BooleanField(default=True)
    texto_encabezado = models.TextField(
        blank=True,
        null=True,
        help_text="Texto adicional en el encabezado de impresiones"
    )
    
    # Pie de página
    texto_pie_pagina = models.TextField(
        blank=True,
        null=True,
        help_text="Texto del pie de página en impresiones"
    )
    mensaje_agradecimiento = models.CharField(
        max_length=200,
        default="¡Gracias por su compra!",
        help_text="Mensaje de agradecimiento en recibos"
    )
    
    # Configuración de formato
    incluir_fecha_hora = models.BooleanField(default=True)
    incluir_numero_ticket = models.BooleanField(default=True)
    incluir_vendedor = models.BooleanField(default=True)
    incluir_metodo_pago = models.BooleanField(default=True)
    
    # Información fiscal
    rfc = models.CharField(max_length=15, blank=True, null=True)
    regimen_fiscal = models.CharField(max_length=200, blank=True, null=True)
    numero_autorizacion = models.CharField(max_length=50, blank=True, null=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Detalles de Impresión"
        verbose_name_plural = "Detalles de Impresión"
        db_table = 'configuracion_impresion'
    
    def __str__(self):
        return f"Impresión: {self.configuracion.nombre_negocio}"
