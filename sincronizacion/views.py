from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.apps import apps
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils.timezone import now, timedelta
from tiendas.models import Tienda

from .models import ColaSincronizacion, ConfiguracionSincronizacion, RegistroSincronizacion, EstadoSincronizacion
from .serializers import (
    ColaSincronizacionSerializer, ConfiguracionSincronizacionSerializer,
    RegistroSincronizacionSerializer, ContentTypeSerializer, RegistroAuditoriaSerializer
)
from .tasks import (
    procesar_cola_sincronizacion, iniciar_sincronizacion_completa,
    verificar_sincronizaciones_automaticas, resolver_conflicto as resolver_conflicto_task
)
from .security import RegistroAuditoria, SeguridadSincronizacion
from .conflict_resolution import ConflictResolver, ConflictResolutionStrategy
from .performance_optimizations import (
    refrescar_cache_incremental, cache_model_batch,
    detectar_conflictos_potenciales, ajustar_prioridades_dinamicas,
    procesar_cola_rapido
)

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
    # Obtener estadísticas para el dashboard
    tienda_actual = Tienda.objects.filter(activa=True).first()
    
    # Contar operaciones pendientes
    pendientes = ColaSincronizacion.objects.filter(
        estado=EstadoSincronizacion.PENDIENTE
    ).count()
    
    # Contar conflictos
    conflictos = ColaSincronizacion.objects.filter(
        tiene_conflicto=True
    ).count()
    
    # Última sincronización exitosa
    ultima_sincronizacion = RegistroSincronizacion.objects.filter(
        exitoso=True
    ).order_by('-fecha_fin').first()
    
    # Estado de conexión (simplificado para esta implementación)
    estado_conexion = 'conectado' if tienda_actual else 'desconectado'
    
    # Estadísticas por tipo de objeto
    estadisticas_por_modelo = ColaSincronizacion.objects.filter(
        estado=EstadoSincronizacion.PENDIENTE
    ).values(
        'content_type__app_label', 
        'content_type__model'
    ).annotate(
        total=Count('id')
    ).order_by('-total')[:5]  # Top 5
    
    # Obtener configuración de sincronización
    configuracion, created = ConfiguracionSincronizacion.objects.get_or_create(
        tienda=tienda_actual,
        defaults={
            'sincronizacion_automatica': True,
            'intervalo_minutos': 15
        }
    )
    
    return render(request, 'sincronizacion/dashboard.html', {
        'pendientes': pendientes,
        'conflictos': conflictos,
        'ultima_sincronizacion': ultima_sincronizacion,
        'estado_conexion': estado_conexion,
        'estadisticas_por_modelo': estadisticas_por_modelo,
        'configuracion': configuracion,
        'tienda_actual': tienda_actual
    })

@login_required
def cola_sincronizacion(request):
    """
    Vista para la cola de sincronización
    """
    # Obtener parámetros de filtrado
    estado = request.GET.get('estado', '')
    modelo = request.GET.get('modelo', '')
    
    # Base query
    operaciones = ColaSincronizacion.objects.all().order_by('-fecha_creacion')
    
    # Aplicar filtros
    if estado:
        operaciones = operaciones.filter(estado=estado)
    
    if modelo and '.' in modelo:
        app_label, model = modelo.split('.')
        try:
            ct = ContentType.objects.get(app_label=app_label, model=model)
            operaciones = operaciones.filter(content_type=ct)
        except ContentType.DoesNotExist:
            pass
    
    # Paginación básica
    operaciones = operaciones[:100]  # Limitar a 100 resultados
    
    # Obtener tipos de contenido para el filtro
    content_types = ContentType.objects.filter(
        colasincronizacion__isnull=False
    ).distinct().order_by('app_label', 'model')
    
    return render(request, 'sincronizacion/cola.html', {
        'operaciones': operaciones,
        'content_types': content_types,
        'estado_seleccionado': estado,
        'modelo_seleccionado': modelo,
        'estados': EstadoSincronizacion.choices
    })

@login_required
def resolver_conflicto(request, operacion_id):
    """
    Vista para resolver conflictos de sincronización
    """
    operacion = get_object_or_404(ColaSincronizacion, id=operacion_id)
    
    # Verificar si realmente hay un conflicto
    if not operacion.tiene_conflicto:
        messages.error(request, 'La operación no tiene conflictos para resolver.')
        return redirect('sincronizacion:cola_sincronizacion')
    
    if request.method == 'POST':
        # Obtener decisión del usuario
        decision = request.POST.get('resolucion', '')
        
        # Importar función de tarea para resolver conflictos
        from .tasks import resolver_conflicto as resolver_conflicto_task
        
        if decision == 'servidor':
            # Usar datos del servidor
            resultado = resolver_conflicto_task(
                operacion_id=operacion.id,
                usar_datos_servidor=True,
                usuario=request.user
            )
        elif decision == 'local':
            # Usar datos locales
            resultado = resolver_conflicto_task(
                operacion_id=operacion.id,
                usar_datos_servidor=False,
                usuario=request.user
            )
        elif decision == 'personalizado':
            # Datos personalizados (simplificado)
            datos_personalizados = request.POST.get('datos_personalizados', '{}')
            import json
            try:
                datos_json = json.loads(datos_personalizados)
                resultado = resolver_conflicto_task(
                    operacion_id=operacion.id,
                    usar_datos_servidor=False,
                    datos_personalizados=datos_json,
                    usuario=request.user
                )
            except json.JSONDecodeError:
                messages.error(request, 'Error en el formato de los datos personalizados.')
                return redirect('sincronizacion:resolver_conflicto', operacion_id=operacion_id)
        else:
            messages.error(request, 'Opción de resolución no válida.')
            return redirect('sincronizacion:resolver_conflicto', operacion_id=operacion_id)
        
        if resultado:
            messages.success(request, 'Conflicto resuelto correctamente.')
            return redirect('sincronizacion:cola_sincronizacion')
        else:
            messages.error(request, 'Error al resolver el conflicto.')
    
    # Obtener modelo y datos
    content_type = operacion.content_type
    model_class = content_type.model_class()
    model_name = f"{content_type.app_label}.{content_type.model}"
    
    # Preparar contexto para la plantilla
    context = {
        'operacion': operacion,
        'model_name': model_name,
        'datos_locales': operacion.datos,
        'datos_servidor': operacion.datos_servidor or {},
        'diferencias': operacion.diferencias or []
    }
    
    return render(request, 'sincronizacion/resolver_conflicto.html', context)

@login_required
def historial_sincronizacion(request):
    """
    Vista para el historial de sincronizaciones
    """
    # Obtener parámetros de filtrado
    desde = request.GET.get('desde', '')
    hasta = request.GET.get('hasta', '')
    
    # Base query
    registros = RegistroSincronizacion.objects.all().order_by('-fecha_inicio')
    
    # Aplicar filtros de fecha
    if desde:
        try:
            from datetime import datetime
            fecha_desde = datetime.strptime(desde, '%Y-%m-%d')
            registros = registros.filter(fecha_inicio__gte=fecha_desde)
        except ValueError:
            pass
    
    if hasta:
        try:
            from datetime import datetime
            fecha_hasta = datetime.strptime(hasta, '%Y-%m-%d')
            registros = registros.filter(fecha_inicio__lte=fecha_hasta)
        except ValueError:
            pass
    
    # Paginación básica
    registros = registros[:100]  # Limitar a 100 resultados
    
    return render(request, 'sincronizacion/historial.html', {
        'registros': registros,
        'desde': desde,
        'hasta': hasta
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
    
    if request.method == 'POST':
        # Actualizar configuración
        sincronizacion_automatica = request.POST.get('sincronizacion_automatica') == 'on'
        intervalo_minutos = int(request.POST.get('intervalo_minutos', 15))
        
        config.sincronizacion_automatica = sincronizacion_automatica
        config.intervalo_minutos = intervalo_minutos
        config.save()
        
        messages.success(request, 'Configuración actualizada correctamente.')
        return redirect('sincronizacion:configuracion_sincronizacion')
    
    return render(request, 'sincronizacion/configuracion.html', {
        'config': config,
    })

@login_required
def sincronizar_ahora(request, config_id):
    """
    Inicia una sincronización manual
    """
    config = get_object_or_404(ConfiguracionSincronizacion, id=config_id)
    
    # Iniciar sincronización
    try:
        iniciar_sincronizacion_completa(config.tienda)
        messages.success(request, 'Sincronización iniciada correctamente.')
    except Exception as e:
        messages.error(request, f'Error al iniciar sincronización: {e}')
    
    return redirect('sincronizacion:sincronizacion_dashboard')

@login_required
def auditoria_sincronizacion(request):
    """
    Vista para consultar los registros de auditoría
    """
    # Obtener parámetros de filtrado
    accion = request.GET.get('accion', '')
    exitoso = request.GET.get('exitoso', '')
    
    # Base query
    registros = RegistroAuditoria.objects.all().order_by('-fecha')
    
    # Aplicar filtros
    if accion:
        registros = registros.filter(accion=accion)
    
    if exitoso in ['true', 'false']:
        registros = registros.filter(exitoso=exitoso == 'true')
    
    # Paginación básica
    registros = registros[:100]  # Limitar a 100 resultados
    
    # Acciones distintas para el filtro
    acciones_distintas = RegistroAuditoria.objects.values_list('accion', flat=True).distinct()
    
    return render(request, 'sincronizacion/auditoria.html', {
        'registros': registros,
        'accion_seleccionada': accion,
        'exitoso_seleccionado': exitoso,
        'acciones_distintas': acciones_distintas
    })

@login_required
def offline_status(request):
    """
    Vista para gestionar el modo offline
    """
    # Obtener tienda actual
    tienda_actual = Tienda.objects.filter(activa=True).first()
    
    # Información sobre datos precargados en caché
    from .cache_manager import cache_manager
    
    # Lista de modelos críticos con conteo
    modelos_criticos = [
        'productos.Producto',
        'productos.Catalogo',
        'clientes.Cliente',
        'inventario.Inventario',
        'descuentos.TabuladorDescuento',
    ]
    
    estadisticas_cache = []
    
    for modelo_str in modelos_criticos:
        app_label, model_name = modelo_str.split('.')
        try:
            model_class = apps.get_model(app_label, model_name)
            
            # Contar registros totales
            total_registros = model_class.objects.count()
            
            # Contar registros en caché
            ids_en_cache = cache_manager.get_persisted_ids(model_class)
            total_en_cache = len(ids_en_cache)
            
            estadisticas_cache.append({
                'modelo': model_name,
                'app': app_label,
                'total': total_registros,
                'en_cache': total_en_cache,
                'porcentaje': (total_en_cache / total_registros * 100) if total_registros > 0 else 0
            })
            
        except Exception as e:
            estadisticas_cache.append({
                'modelo': model_name,
                'app': app_label,
                'error': str(e),
                'total': 0,
                'en_cache': 0,
                'porcentaje': 0
            })
    
    if request.method == 'POST' and request.POST.get('action') == 'update_cache':
        modelo = request.POST.get('modelo')
        if modelo and '.' in modelo:
            app_label, model_name = modelo.split('.')
            try:
                model_class = apps.get_model(app_label, model_name)
                total = cache_model_batch(model_class)
                messages.success(request, f'Se han actualizado {total} registros en la caché para {model_name}.')
            except Exception as e:
                messages.error(request, f'Error al actualizar caché: {e}')
        
        return redirect('sincronizacion:offline_status')
    
    return render(request, 'sincronizacion/offline.html', {
        'tienda': tienda_actual,
        'estadisticas_cache': estadisticas_cache
    })

class RegistroAuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar los registros de auditoría de seguridad"""
    queryset = RegistroAuditoria.objects.all().order_by('-fecha')
    serializer_class = RegistroAuditoriaSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filterset_fields = ['tienda', 'usuario', 'accion', 'exitoso']
    search_fields = ['accion', 'detalles']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por rango de fechas
        fecha_inicio = self.request.query_params.get('fecha_inicio')
        fecha_fin = self.request.query_params.get('fecha_fin')
        
        if fecha_inicio:
            try:
                from datetime import datetime
                fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                queryset = queryset.filter(fecha__gte=fecha_inicio_dt)
            except ValueError:
                pass
                
        if fecha_fin:
            try:
                from datetime import datetime
                fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
                queryset = queryset.filter(fecha__lte=fecha_fin_dt)
            except ValueError:
                pass
                
        return queryset
