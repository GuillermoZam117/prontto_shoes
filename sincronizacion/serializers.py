from rest_framework import serializers
from .models import ColaSincronizacion, ConfiguracionSincronizacion, RegistroSincronizacion
from django.contrib.contenttypes.models import ContentType
from tiendas.serializers import TiendaSerializer
from django.contrib.auth import get_user_model
from .security import RegistroAuditoria

UserModel = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['id', 'username', 'first_name', 'last_name']


class ColaSincronizacionSerializer(serializers.ModelSerializer):
    tienda_origen_detail = TiendaSerializer(source='tienda_origen', read_only=True)
    tienda_destino_detail = TiendaSerializer(source='tienda_destino', read_only=True)
    content_type_nombre = serializers.SerializerMethodField()
    resuelto_por_detail = UserMinimalSerializer(source='resuelto_por', read_only=True)
    
    class Meta:
        model = ColaSincronizacion
        fields = '__all__'
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion', 'intentos']
    
    def get_content_type_nombre(self, obj):
        return f"{obj.content_type.app_label}.{obj.content_type.model}"
    
    def to_representation(self, instance):
        """
        Customizes the data representation to avoid too much nested data
        """
        ret = super().to_representation(instance)
        
        # Parse the datos field if it's a JSON string, otherwise leave it as is
        if isinstance(ret['datos'], str):
            try:
                import json
                ret['datos'] = json.loads(ret['datos'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        return ret


class ConfiguracionSincronizacionSerializer(serializers.ModelSerializer):
    tienda_detail = TiendaSerializer(source='tienda', read_only=True)
    
    class Meta:
        model = ConfiguracionSincronizacion
        fields = '__all__'
        read_only_fields = ['ultima_sincronizacion']


class RegistroSincronizacionSerializer(serializers.ModelSerializer):
    tienda_detail = TiendaSerializer(source='tienda', read_only=True)
    iniciado_por_detail = UserMinimalSerializer(source='iniciado_por', read_only=True)
    duracion_minutos = serializers.SerializerMethodField()
    
    class Meta:
        model = RegistroSincronizacion
        fields = '__all__'
        read_only_fields = ['fecha_inicio', 'fecha_fin', 'operaciones_totales', 
                           'operaciones_exitosas', 'operaciones_fallidas', 
                           'operaciones_con_conflicto', 'resumen', 'estado']
    
    def get_duracion_minutos(self, obj):
        return obj.calcular_duracion()


class ContentTypeSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model', 'nombre_completo']
    
    def get_nombre_completo(self, obj):
        return f"{obj.app_label}.{obj.model}"


class RegistroAuditoriaSerializer(serializers.ModelSerializer):
    """Serializer para el modelo RegistroAuditoria"""
    tienda_detail = TiendaSerializer(source='tienda', read_only=True)
    usuario_detail = UserMinimalSerializer(source='usuario', read_only=True)
    content_type_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = RegistroAuditoria
        fields = '__all__'
        read_only_fields = ['fecha', 'usuario', 'tienda', 'accion', 'content_type', 
                           'object_id', 'ip_origen', 'detalles', 'exitoso']
    
    def get_content_type_nombre(self, obj):
        if obj.content_type:
            return f"{obj.content_type.app_label}.{obj.content_type.model}"
        return None
