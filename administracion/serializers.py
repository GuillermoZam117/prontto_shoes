from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from .models import LogAuditoria, PerfilUsuario, ConfiguracionSistema

User = get_user_model()

class LogAuditoriaSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    accion_display = serializers.CharField(source='get_accion_display', read_only=True)
    
    class Meta:
        model = LogAuditoria
        fields = '__all__'

class PerfilUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilUsuario
        fields = '__all__'

class UsuarioSerializer(serializers.ModelSerializer):
    perfil = PerfilUsuarioSerializer(read_only=True)
    grupos = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'is_active', 'is_staff', 'date_joined', 'last_login', 
                 'grupos', 'perfil']
        extra_kwargs = {
            'password': {'write_only': True}
        }

class GrupoSerializer(serializers.ModelSerializer):
    permisos_count = serializers.SerializerMethodField()
    usuarios_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions', 'permisos_count', 'usuarios_count']
    
    def get_permisos_count(self, obj):
        return obj.permissions.count()
    
    def get_usuarios_count(self, obj):
        return obj.user_set.count()

class PermisoSerializer(serializers.ModelSerializer):
    content_type_name = serializers.CharField(source='content_type.name', read_only=True)
    
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type', 'content_type_name']

class ConfiguracionSistemaSerializer(serializers.ModelSerializer):
    modificado_por_username = serializers.CharField(source='modificado_por.username', read_only=True)
    
    class Meta:
        model = ConfiguracionSistema
        fields = '__all__'
