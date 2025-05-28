from rest_framework import serializers
from .models import ConfiguracionNegocio, InformacionContacto, DetallesImpresion


class ConfiguracionNegocioSerializer(serializers.ModelSerializer):
    """Serializer para la configuración del negocio"""
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ConfiguracionNegocio
        fields = [
            'id',
            'nombre_negocio',
            'eslogan',
            'descripcion',
            'logo',
            'logo_url',
            'logo_texto',
            'sidebar_collapsed_default',
            'sidebar_theme',
            'color_primario',
            'color_secundario',
            'moneda',
            'simbolo_moneda',
            'timezone',
            'idioma',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'logo_url']
    
    def get_logo_url(self, obj):
        """Obtener URL completa del logo"""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
    
    def validate_color_primario(self, value):
        """Validar formato hexadecimal del color primario"""
        if value and not value.startswith('#'):
            raise serializers.ValidationError("El color debe estar en formato hexadecimal (#000000)")
        if value and len(value) != 7:
            raise serializers.ValidationError("El color debe tener 6 dígitos hexadecimales (#000000)")
        return value
    
    def validate_color_secundario(self, value):
        """Validar formato hexadecimal del color secundario"""
        if value and not value.startswith('#'):
            raise serializers.ValidationError("El color debe estar en formato hexadecimal (#000000)")
        if value and len(value) != 7:
            raise serializers.ValidationError("El color debe tener 6 dígitos hexadecimales (#000000)")
        return value


class InformacionContactoSerializer(serializers.ModelSerializer):
    """Serializer para información de contacto"""
    
    class Meta:
        model = InformacionContacto
        fields = [
            'id',
            'direccion_linea1',
            'direccion_linea2',
            'ciudad',
            'estado_provincia',
            'codigo_postal',
            'pais',
            'telefono_principal',
            'telefono_secundario',
            'email_principal',
            'email_ventas',
            'email_soporte',
            'sitio_web',
            'facebook',
            'instagram',
            'twitter',
            'whatsapp',
            'horario_atencion',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DetallesImpresionSerializer(serializers.ModelSerializer):
    """Serializer para detalles de impresión"""
    
    class Meta:
        model = DetallesImpresion
        fields = [
            'id',
            'mostrar_logo_impresion',
            'texto_encabezado',
            'texto_pie_pagina',
            'mensaje_agradecimiento',
            'incluir_fecha_hora',
            'incluir_numero_ticket',
            'incluir_vendedor',
            'incluir_metodo_pago',
            'rfc',
            'regimen_fiscal',
            'numero_autorizacion',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LogotipoSerializer(serializers.Serializer):
    """Serializer específico para manejo de logotipo"""
    logo = serializers.ImageField(required=True)
    logo_texto = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_logo(self, value):
        """Validar el archivo de logo"""
        # Validar tamaño (máximo 2MB)
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("El logo no puede ser mayor a 2MB")
        
        # Validar tipo de archivo
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/svg+xml']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Solo se permiten archivos JPG, PNG o SVG")
        
        return value


class ConfiguracionCompletaSerializer(serializers.ModelSerializer):
    """Serializer completo con toda la configuración del negocio"""
    contacto = InformacionContactoSerializer(read_only=True)
    impresion = DetallesImpresionSerializer(read_only=True)
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ConfiguracionNegocio
        fields = [
            'id',
            'nombre_negocio',
            'eslogan',
            'descripcion',
            'logo',
            'logo_url',
            'logo_texto',
            'sidebar_collapsed_default',
            'sidebar_theme',
            'color_primario',
            'color_secundario',
            'moneda',
            'simbolo_moneda',
            'timezone',
            'idioma',
            'contacto',
            'impresion',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'logo_url', 'contacto', 'impresion']
    
    def get_logo_url(self, obj):
        """Obtener URL completa del logo"""
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None
