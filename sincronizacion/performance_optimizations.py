"""
Mejoras de rendimiento para el módulo de sincronización.

Este módulo implementa las optimizaciones de rendimiento descritas
en OPTIMIZACIONES_RENDIMIENTO.md.
"""
import logging
import asyncio
from asgiref.sync import async_to_sync
from django.apps import apps
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from .cache_manager import cache_manager
from .signals import MODELOS_SINCRONIZABLES
from .models import ColaSincronizacion, EstadoSincronizacion, ConfiguracionSincronizacion
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)

def refrescar_cache_incremental():
    """
    Refresca la caché de forma incremental, actualizando solo los datos
    que han cambiado desde la última actualización.
    """
    ultima_actualizacion = cache.get('sync_cache_last_refresh')
    if not ultima_actualizacion:
        # Si no hay marca de tiempo, usar 7 días atrás como valor predeterminado
        ultima_actualizacion = timezone.now() - timedelta(days=7)
    
    logger.info(f"Iniciando refresco incremental de caché desde {ultima_actualizacion}")
    
    total_actualizados = 0
    
    for modelo_path, config in MODELOS_SINCRONIZABLES.items():
        try:
            app_label, model_name = modelo_path.split('.')
            model_class = apps.get_model(app_label, model_name)
            
            # Determinar campo de fecha de actualización
            # Asumimos que el modelo tiene un campo 'updated_at' o similar
            update_field = getattr(model_class, 'SYNC_UPDATE_FIELD', 'updated_at')
            
            # Construir filtro para obtener solo registros actualizados
            filter_kwargs = {f"{update_field}__gt": ultima_actualizacion}
            
            nuevos_registros = model_class.objects.filter(**filter_kwargs)
            count = nuevos_registros.count()
            
            logger.info(f"Refrescando caché para {count} registros de {modelo_path}")
            
            # Actualizar caché para estos registros
            for instance in nuevos_registros:
                cache_manager.cache_model_instance(instance)
            
            total_actualizados += count
            
        except Exception as e:
            logger.error(f"Error al refrescar caché incremental para {modelo_path}: {e}")
    
    # Actualizar marca de tiempo
    cache.set('sync_cache_last_refresh', timezone.now())
    
    logger.info(f"Refresco incremental de caché completado. {total_actualizados} registros actualizados.")
    return total_actualizados

def cache_model_batch(model_class, queryset=None, batch_size=100):
    """
    Almacena instancias de modelo en la caché por lotes para mejorar rendimiento
    """
    from .signals import obtener_config_modelo, serializar_instancia
    
    if queryset is None:
        queryset = model_class.objects.all()
    
    total_registros = queryset.count()
    logger.info(f"Iniciando caché por lotes para {total_registros} registros de {model_class.__name__}")
    
    config = obtener_config_modelo(model_class)
    excluded_fields = config.get('excluded_fields', [])
    essential_fields = config.get('essential_fields', None)
    
    # Determinar función de serialización basada en configuración
    if essential_fields:
        serialize_func = lambda inst: serializar_instancia_campos(inst, essential_fields)
    else:
        serialize_func = lambda inst: serializar_instancia(inst, excluded_fields)
    
    # Procesar en lotes
    for i in range(0, total_registros, batch_size):
        batch = queryset[i:i+batch_size]
        batch_data = {}
        
        for instance in batch:
            key = cache_manager.get_cache_key(model_class, instance.pk)
            datos = serialize_func(instance)
            batch_data[key] = datos
        
        # Almacenar lote en caché
        cache.set_many(batch_data, cache_manager.DEFAULT_CACHE_TTL)
        
        # Persistir registros críticos
        if cache_manager.es_modelo_critico(model_class):
            for key, datos in batch_data.items():
                cache_manager.persist_to_disk(key, datos)
        
        logger.debug(f"Procesado lote {i}-{i+len(batch)} de {total_registros} para {model_class.__name__}")
    
    logger.info(f"Caché por lotes completada para {model_class.__name__}")
    return total_registros

def serializar_instancia_campos(instance, campos):
    """
    Serializa solo los campos especificados de una instancia
    """
    resultado = {}
    
    for campo in campos:
        try:
            valor = getattr(instance, campo)
            
            # Convertir tipos complejos
            if hasattr(valor, 'isoformat'):  # Es una fecha/hora
                valor = valor.isoformat()
            
            resultado[campo] = valor
        except Exception as e:
            logger.warning(f"Error al serializar campo {campo} de {instance}: {e}")
    
    return resultado

async def procesar_cola_asincrono(tienda_id=None, limit=None):
    """
    Procesa la cola de sincronización de forma asíncrona para mayor rendimiento
    """
    from .tasks import procesar_operacion
    
    # Obtener operaciones pendientes
    operaciones = ColaSincronizacion.objects.filter(
        estado=EstadoSincronizacion.PENDIENTE
    ).order_by('prioridad')
    
    if tienda_id:
        operaciones = operaciones.filter(tienda_origen_id=tienda_id)
    
    if limit:
        operaciones = operaciones[:limit]
    
    total_operaciones = operaciones.count()
    logger.info(f"Iniciando procesamiento asíncrono de {total_operaciones} operaciones")
    
    # Definir función coroutine para procesar operación
    async def procesar_async(op_id):
        # Convertir la función síncrona a asíncrona
        return await asyncio.to_thread(procesar_operacion, op_id)
    
    # Procesar en paralelo (hasta 5 operaciones simultáneas)
    semaphore = asyncio.Semaphore(5)  # Limitar concurrencia
    
    async def procesar_con_limite(op_id):
        async with semaphore:
            return await procesar_async(op_id)
    
    # Crear tareas
    tareas = [procesar_con_limite(op.id) for op in operaciones]
    
    # Ejecutar tareas
    resultados = await asyncio.gather(*tareas, return_exceptions=True)
    
    # Contar resultados
    exitos = sum(1 for r in resultados if r is True)
    errores = sum(1 for r in resultados if isinstance(r, Exception))
    
    logger.info(f"Procesamiento asíncrono completado: {exitos} éxitos, {errores} errores")
    return exitos, errores

def procesar_cola_rapido(tienda_id=None, limit=None):
    """Wrapper para llamar a la función asíncrona desde código síncrono"""
    return async_to_sync(procesar_cola_asincrono)(tienda_id, limit)

def ajustar_prioridades_dinamicas():
    """
    Ajusta dinámicamente las prioridades de sincronización basado en patrones de uso
    """
    from django.db.models import Count
    
    # Identificar modelos con más operaciones en los últimos 7 días
    ahora = timezone.now()
    una_semana_atras = ahora - timedelta(days=7)
    
    logger.info("Iniciando ajuste dinámico de prioridades")
    
    stats = ColaSincronizacion.objects.filter(
        fecha_creacion__gte=una_semana_atras
    ).values('content_type').annotate(
        total=Count('id')
    ).order_by('-total')
    
    # Ajustar prioridades en configuración
    for i, stat in enumerate(stats):
        content_type = ContentType.objects.get(id=stat['content_type'])
        modelo_path = f"{content_type.app_label}.{content_type.model}"
        
        # Actualizar prioridad (menor número = mayor prioridad)
        try:
            config = ConfiguracionSincronizacion.objects.get(tienda__activa=True)
            prioridades = config.prioridades or {}
            nueva_prioridad = i + 1  # prioridad basada en frecuencia
            prioridad_anterior = prioridades.get(modelo_path, 999)
            
            # Actualizar solo si hay un cambio significativo
            if abs(nueva_prioridad - prioridad_anterior) > 2:
                logger.info(f"Ajustando prioridad para {modelo_path}: {prioridad_anterior} -> {nueva_prioridad}")
                prioridades[modelo_path] = nueva_prioridad
                config.prioridades = prioridades
                config.save()
        except ConfiguracionSincronizacion.DoesNotExist:
            logger.warning("No se encontró configuración de sincronización para ajustar prioridades")
    
    logger.info("Ajuste dinámico de prioridades completado")
    return True

def detectar_conflictos_potenciales(operacion):
    """
    Detecta conflictos potenciales antes de procesar una operación
    """
    from django.db.models import Q
    
    # Buscar operaciones relacionadas con el mismo objeto
    conflictos_potenciales = ColaSincronizacion.objects.filter(
        ~Q(id=operacion.id),
        content_type=operacion.content_type,
        object_id=operacion.object_id,
        estado__in=[EstadoSincronizacion.PENDIENTE, EstadoSincronizacion.PROCESANDO]
    )
    
    return conflictos_potenciales.exists()

def resolver_conflicto_campo_a_campo(conflicto_a, conflicto_b, reglas_por_campo):
    """
    Resuelve conflictos campo por campo según reglas específicas
    """
    datos_a = conflicto_a.datos
    datos_b = conflicto_b.datos
    datos_resueltos = {}
    
    for campo, regla in reglas_por_campo.items():
        if regla == 'mayor_valor':
            datos_resueltos[campo] = max(datos_a.get(campo, 0), datos_b.get(campo, 0))
        elif regla == 'menor_valor':
            datos_resueltos[campo] = min(datos_a.get(campo, 0), datos_b.get(campo, 0))
        elif regla == 'concatenar':
            datos_resueltos[campo] = f"{datos_a.get(campo, '')} | {datos_b.get(campo, '')}"
        elif regla == 'prioridad_central':
            datos_resueltos[campo] = datos_a.get(campo) if conflicto_a.tienda_origen.es_central else datos_b.get(campo)
        else:  # por defecto, último en modificar
            datos_resueltos[campo] = datos_a.get(campo) if conflicto_a.fecha_creacion > conflicto_b.fecha_creacion else datos_b.get(campo)
    
    return datos_resueltos
