from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.apps import apps
from tiendas.models import Tienda

from .models import ColaSincronizacion, ConfiguracionSincronizacion, RegistroSincronizacion, EstadoSincronizacion
from .serializers import (
    ColaSincronizacionSerializer, ConfiguracionSincronizacionSerializer,
    RegistroSincronizacionSerializer, ContentTypeSerializer, RegistroAuditoriaSerializer
)
from .tasks import (
    procesar_cola_sincronizacion, iniciar_sincronizacion_completa,
    verificar_sincronizaciones_automaticas, resolver_conflicto
)
from .security import RegistroAuditoria, SeguridadSincronizacion

class ColaSincronizacionViewSet(viewsets.ModelViewSet):
    queryset = ColaSincronizacion.objects.all().order_by('-fecha_creacion')
    serializer_class = ColaSincronizacionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['estado', 'tipo_operacion', 'tienda_origen', 'tienda_destino', 'tiene_conflicto']
    search_fields = ['object_id', 'error_mensaje']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por content_type si se proporciona
        content_type_id = self.request.query_params.get('content_type')
        if content_type_id:
            queryset = queryset.filter(content_type_id=content_type_id)
        
        # Filtrar por modelo (app_label.model)
        modelo = self.request.query_params.get('modelo')
        if modelo and '.' in modelo:
            app_label, model = modelo.split('.')
            try:
                ct = ContentType.objects.get(app_label=app_label, model=model)
                queryset = queryset.filter(content_type=ct)
            except ContentType.DoesNotExist:
                pass
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def procesar(self, request, pk=None):
        """Procesa una operación específica de la cola"""
        operacion = self.get_object()
        
        if operacion.estado == EstadoSincronizacion.COMPLETADO:
            return Response({'detail': 'La operación ya fue completada'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Iniciar procesamiento
        resultado = procesar_cola_sincronizacion(operacion_id=operacion.id)
        
        # Recargar para obtener el estado actualizado
        operacion.refresh_from_db()
        
        return Response({
            'detail': 'Operación procesada',
            'resultado': resultado,
            'estado_actual': operacion.estado
        })
    
    @action(detail=True, methods=['post'])
    def resolver(self, request, pk=None):
        """Resuelve un conflicto de sincronización"""
        operacion = self.get_object()
        
        if not operacion.tiene_conflicto:
            return Response({'detail': 'La operación no tiene conflictos'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Determinar estrategia de resolución
        usar_datos_servidor = request.data.get('usar_datos_servidor', True)
        datos_personalizados = request.data.get('datos_personalizados')
        
        # Resolver conflicto
        resultado = resolver_conflicto(
            operacion.id, 
            usar_datos_servidor=usar_datos_servidor,
            datos_personalizados=datos_personalizados,
            usuario=request.user
        )
        
        # Recargar para obtener el estado actualizado
        operacion.refresh_from_db()
        
        return Response({
            'detail': 'Conflicto resuelto' if resultado else 'Error al resolver conflicto',
            'resultado': resultado,
            'estado_actual': operacion.estado
        })
    
    @action(detail=False, methods=['post'])
    def procesar_pendientes(self, request):
        """Procesa todas las operaciones pendientes"""
        tienda_id = request.data.get('tienda_id')
        max_items = request.data.get('max_items', 100)
        
        exitosas, fallidas, conflictos = procesar_cola_sincronizacion(
            tienda_id=tienda_id,
            max_items=max_items
        )
        
        return Response({
            'detail': 'Procesamiento completado',
            'exitosas': exitosas,
            'fallidas': fallidas,
            'conflictos': conflictos
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtiene estadísticas de la cola de sincronización"""
        # Total por estado
        por_estado = ColaSincronizacion.objects.values('estado').annotate(total=Count('id'))
        
        # Total por content_type para pendientes
        pendientes_por_modelo = ColaSincronizacion.objects.filter(
            estado=EstadoSincronizacion.PENDIENTE
        ).values(
            'content_type__app_label', 
            'content_type__model'
        ).annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Conflictos
        conflictos = ColaSincronizacion.objects.filter(tiene_conflicto=True).count()
        
        # Antigüedad del pendiente más viejo
        try:
            mas_antiguo = ColaSincronizacion.objects.filter(
                estado=EstadoSincronizacion.PENDIENTE
            ).order_by('fecha_creacion').first()
            
            if mas_antiguo:
                antiguedad = (timezone.now() - mas_antiguo.fecha_creacion).total_seconds() / 60  # en minutos
            else:
                antiguedad = 0
        except:
            antiguedad = 0
        
        return Response({
            'por_estado': por_estado,
            'pendientes_por_modelo': pendientes_por_modelo,
            'conflictos': conflictos,
            'antiguedad_minutos': round(antiguedad, 2)
        })


class ConfiguracionSincronizacionViewSet(viewsets.ModelViewSet):
    queryset = ConfiguracionSincronizacion.objects.all()
    serializer_class = ConfiguracionSincronizacionSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def sincronizar_ahora(self, request, pk=None):
        """Inicia una sincronización completa para la tienda"""
        config = self.get_object()
        
        registro_id = iniciar_sincronizacion_completa(config.tienda.id, usuario=request.user)
        
        if registro_id:
            return Response({
                'detail': 'Sincronización iniciada',
                'registro_id': registro_id
            })
        else:
            return Response({
                'detail': 'Error al iniciar sincronización'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegistroSincronizacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RegistroSincronizacion.objects.all().order_by('-fecha_inicio')
    serializer_class = RegistroSincronizacionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['tienda', 'estado']


class ContentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para listar los tipos de contenido (modelos) disponibles para sincronización"""
    queryset = ContentType.objects.all().order_by('app_label', 'model')
    serializer_class = ContentTypeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por app_label
        app_label = self.request.query_params.get('app_label')
        if app_label:
            queryset = queryset.filter(app_label=app_label)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def sincronizables(self, request):
        """Lista los tipos de contenido que son sincronizables"""
        from .signals import MODELOS_SINCRONIZABLES
        
        modelos = []
        for modelo_str in MODELOS_SINCRONIZABLES:
            if '.' in modelo_str:
                app_label, model = modelo_str.split('.')
                try:
                    ct = ContentType.objects.get(app_label=app_label, model=model.lower())
                    modelos.append(self.serializer_class(ct).data)
                except ContentType.DoesNotExist:
                    pass
        
        return Response(modelos)

# Frontend views
@login_required
def sincronizacion_dashboard(request):
    """
    Vista principal del panel de sincronización
    """
    # Obtener tienda actual (para un sistema multitienda)
    tienda_actual = Tienda.objects.filter(activa=True).first()
    
    # Obtener contadores de operaciones
    pendientes = ColaSincronizacion.objects.filter(
        estado=EstadoSincronizacion.PENDIENTE, 
        tienda_origen=tienda_actual
    ).count()
    
    conflictos = ColaSincronizacion.objects.filter(
        tiene_conflicto=True,
        tienda_origen=tienda_actual
    ).count()
    
    # Obtener configuración de sincronización
    try:
        config = ConfiguracionSincronizacion.objects.get(tienda=tienda_actual)
    except ConfiguracionSincronizacion.DoesNotExist:
        config = None
    
    # Obtener última sincronización exitosa
    ultima_sync = RegistroSincronizacion.objects.filter(
        tienda=tienda_actual,
        estado=EstadoSincronizacion.COMPLETADO
    ).order_by('-fecha_fin').first()
    
    return render(request, 'sincronizacion/dashboard.html', {
        'tienda_actual': tienda_actual,
        'pendientes': pendientes,
        'conflictos': conflictos,
        'config': config,
        'ultima_sincronizacion': ultima_sync,
    })

@login_required
def cola_sincronizacion(request):
    """
    Vista para ver y gestionar la cola de sincronización
    """
    return render(request, 'sincronizacion/cola.html')

@login_required
def resolver_conflicto(request, operacion_id):
    """
    Vista para resolver un conflicto de sincronización específico
    """
    operacion = ColaSincronizacion.objects.get(id=operacion_id, tiene_conflicto=True)
    
    return render(request, 'sincronizacion/resolver_conflicto.html', {
        'operacion': operacion,
    })

@login_required
def historial_sincronizacion(request):
    """
    Vista para ver el historial de sincronizaciones
    """
    # Obtener tienda actual
    tienda_actual = Tienda.objects.filter(activa=True).first()
    
    # Obtener registros de sincronización para esta tienda
    registros = RegistroSincronizacion.objects.filter(
        tienda=tienda_actual
    ).order_by('-fecha_inicio')
    
    return render(request, 'sincronizacion/historial.html', {
        'registros': registros,
    })

@login_required
def configuracion_sincronizacion(request):
    """
    Vista para configurar el comportamiento de sincronización
    """
    # Obtener tienda actual
    tienda_actual = Tienda.objects.filter(activa=True).first()
    
    # Obtener o crear configuración
    config, created = ConfiguracionSincronizacion.objects.get_or_create(
        tienda=tienda_actual,
        defaults={
            'sincronizacion_automatica': True,
            'intervalo_minutos': 15
        }
    )
    
    return render(request, 'sincronizacion/configuracion.html', {
        'config': config,
    })

@login_required
def auditoria_sincronizacion(request):
    """
    Vista para ver el registro de auditoría de sincronización
    """
    # Obtener tienda actual
    tienda_actual = Tienda.objects.filter(activa=True).first()
    
    # Obtener registros de auditoría para esta tienda
    registros = RegistroAuditoria.objects.filter(
        tienda=tienda_actual
    ).order_by('-fecha')[:100]  # Limitar a los últimos 100 registros
    
    return render(request, 'sincronizacion/auditoria.html', {
        'registros': registros,
    })

@login_required
def offline_status(request):
    """
    Vista para verificar y gestionar el estado offline
    """
    from .cache_manager import cache_manager, detectar_estado_conexion
    
    # Determinar si estamos en modo offline
    modo_offline = not detectar_estado_conexion()
    
    # Obtener tienda actual
    tienda_actual = Tienda.objects.filter(activa=True).first()
    
    # Obtener modelos cacheados (para modo offline)
    from .signals import MODELOS_SINCRONIZABLES
    modelos_criticos = []
    
    for modelo_str in MODELOS_SINCRONIZABLES:
        if cache_manager.es_modelo_critico(modelo_str):
            app_label, model_name = modelo_str.split('.')
            model_class = apps.get_model(app_label, model_name)
            
            # Contar registros en caché
            cached_instances = cache_manager.get_cached_queryset(model_class)
            
            modelos_criticos.append({
                'nombre': modelo_str,
                'cached_count': len(cached_instances) if cached_instances else 0,
                'total_count': model_class.objects.count()
            })
    
    return render(request, 'sincronizacion/offline.html', {
        'tienda_actual': tienda_actual,
        'modo_offline': modo_offline,
        'modelos_criticos': modelos_criticos,
    })

class RegistroAuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para el modelo RegistroAuditoria"""
    queryset = RegistroAuditoria.objects.all().order_by('-fecha')
    serializer_class = RegistroAuditoriaSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields = ['tienda', 'accion', 'exitoso']
    search_fields = ['accion', 'detalles']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por fecha
        fecha_desde = self.request.query_params.get('fecha_desde')
        if fecha_desde:
            try:
                from django.utils.dateparse import parse_datetime
                fecha_desde = parse_datetime(fecha_desde)
                if fecha_desde:
                    queryset = queryset.filter(fecha__gte=fecha_desde)
            except:
                pass
        
        fecha_hasta = self.request.query_params.get('fecha_hasta')
        if fecha_hasta:
            try:
                from django.utils.dateparse import parse_datetime
                fecha_hasta = parse_datetime(fecha_hasta)
                if fecha_hasta:
                    queryset = queryset.filter(fecha__lte=fecha_hasta)
            except:
                pass
        
        # Filtrar por usuario
        usuario_id = self.request.query_params.get('usuario_id')
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Obtiene estadísticas de las operaciones de auditoría"""
        # Total por acción
        por_accion = RegistroAuditoria.objects.values('accion').annotate(total=Count('id'))
        
        # Éxitos vs. errores
        exitosos = RegistroAuditoria.objects.filter(exitoso=True).count()
        fallidos = RegistroAuditoria.objects.filter(exitoso=False).count()
        
        # Por tienda
        por_tienda = RegistroAuditoria.objects.values(
            'tienda__id', 
            'tienda__nombre'
        ).annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Por tiempo
        from django.db.models.functions import TruncDay
        por_dia = RegistroAuditoria.objects.annotate(
            dia=TruncDay('fecha')
        ).values('dia').annotate(
            total=Count('id')
        ).order_by('-dia')[:7]  # últimos 7 días
        
        return Response({
            'por_accion': por_accion,
            'exitosos': exitosos,
            'fallidos': fallidos,
            'por_tienda': por_tienda,
            'por_dia': por_dia
        })
