from rest_framework import serializers
from .models import ReportePersonalizado, EjecucionReporte

class ReportePersonalizadoSerializer(serializers.ModelSerializer):
    creado_por_username = serializers.CharField(source='creado_por.username', read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    total_ejecuciones = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportePersonalizado
        fields = '__all__'
        read_only_fields = ('creado_por', 'fecha_creacion', 'ultima_ejecucion')
    
    def get_total_ejecuciones(self, obj):
        return obj.ejecuciones.count()

class EjecucionReporteSerializer(serializers.ModelSerializer):
    ejecutado_por_username = serializers.CharField(source='ejecutado_por.username', read_only=True)
    reporte_nombre = serializers.CharField(source='reporte.nombre', read_only=True)
    reporte_tipo = serializers.CharField(source='reporte.tipo', read_only=True)
    
    class Meta:
        model = EjecucionReporte
        fields = '__all__'
        read_only_fields = ('ejecutado_por', 'fecha_ejecucion', 'tiempo_ejecucion')

class ReporteEjecutarSerializer(serializers.Serializer):
    """Serializer para ejecutar reportes con parámetros"""
    tipo_reporte = serializers.ChoiceField(choices=ReportePersonalizado.TIPO_CHOICES)
    fecha_desde = serializers.DateField(required=False)
    fecha_hasta = serializers.DateField(required=False)
    tienda_id = serializers.IntegerField(required=False)
    cliente_id = serializers.IntegerField(required=False)
    producto_id = serializers.IntegerField(required=False)
    vendedor_id = serializers.IntegerField(required=False)
    limite_registros = serializers.IntegerField(default=1000, min_value=1, max_value=10000)
    formato_salida = serializers.ChoiceField(
        choices=[('json', 'JSON'), ('csv', 'CSV'), ('excel', 'Excel')],
        default='json'
    )
    
    def validate(self, attrs):
        """Validar que las fechas sean consistentes"""
        fecha_desde = attrs.get('fecha_desde')
        fecha_hasta = attrs.get('fecha_hasta')
        
        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                raise serializers.ValidationError(
                    "La fecha desde no puede ser mayor que la fecha hasta"
                )
        
        return attrs
