import logging
import json
import time
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from .models import (
    ColaSincronizacion, RegistroSincronizacion, ConfiguracionSincronizacion,
    EstadoSincronizacion, TipoOperacion
)

logger = logging.getLogger(__name__)

def procesar_cola_sincronizacion(operacion_id=None, tienda_id=None, max_items=100, 
                              registro_sincronizacion=None, simular=False):
    """
    Procesa operaciones pendientes de sincronización, puede filtrar por tienda o por ID específico
    """
    # Establecer filtros
    filtros = Q(estado=EstadoSincronizacion.PENDIENTE)
    
    if operacion_id:
        filtros &= Q(id=operacion_id)
    
    if tienda_id:
        filtros &= Q(tienda_origen_id=tienda_id)
    
    # Obtener operaciones pendientes ordenadas por prioridad
    operaciones = ColaSincronizacion.objects.filter(filtros).order_by('prioridad', 'fecha_creacion')[:max_items]
    
    if not operaciones:
        logger.info("No hay operaciones pendientes para procesar")
        return 0, 0, 0
    
    exitosas = 0
    fallidas = 0
    conflictos = 0
    
    for operacion in operaciones:
        if procesar_operacion(operacion, simular=simular):
            exitosas += 1
        elif operacion.estado == EstadoSincronizacion.CONFLICTO:
            conflictos += 1
        else:
            fallidas += 1
    
    # Actualizar el registro de sincronización si se proporcionó
    if registro_sincronizacion:
        registro_sincronizacion.finalizar(exitosas, fallidas, conflictos)
    
    return exitosas, fallidas, conflictos

def procesar_operacion(operacion, simular=False):
    """
    Procesa una operación específica de la cola de sincronización
    """
    if simular:
        # Modo simulación, solo para pruebas
        time.sleep(0.1)  # Simular algún procesamiento
        return True
    
    try:
        # Marcar como en proceso
        operacion.marcar_en_proceso()
        
        # Obtener el modelo y la clase
        content_type = operacion.content_type
        modelo_clase = content_type.model_class()
        
        if not modelo_clase:
            operacion.marcar_error(f"No se pudo encontrar el modelo {content_type}")
            return False
        
        # Obtener el ID del objeto
        object_id = operacion.object_id
        
        # Procesar según el tipo de operación
        if operacion.tipo_operacion == TipoOperacion.CREAR:
            return crear_objeto(operacion, modelo_clase, object_id)
        
        elif operacion.tipo_operacion == TipoOperacion.ACTUALIZAR:
            return actualizar_objeto(operacion, modelo_clase, object_id)
        
        elif operacion.tipo_operacion == TipoOperacion.ELIMINAR:
            return eliminar_objeto(operacion, modelo_clase, object_id)
        
        else:
            operacion.marcar_error(f"Tipo de operación desconocido: {operacion.tipo_operacion}")
            return False
            
    except Exception as e:
        logger.error(f"Error al procesar operación {operacion.id}: {e}", exc_info=True)
        operacion.marcar_error(str(e))
        return False

def crear_objeto(operacion, modelo_clase, object_id):
    """
    Crea un nuevo objeto según los datos de la operación
    """
    with transaction.atomic():
        try:
            # Verificar si ya existe (podría ser una operación duplicada)
            if modelo_clase.objects.filter(pk=object_id).exists():
                # El objeto ya existe, convertir a actualización
                return actualizar_objeto(operacion, modelo_clase, object_id)
            
            # Obtener los datos y preparar
            datos = operacion.datos
            
            # Eliminar el id del diccionario si existe para crear con PK específica
            datos_copy = datos.copy()
            if 'id' in datos_copy:
                datos_copy.pop('id')
            
            # Crear el objeto con el ID original
            objeto = modelo_clase(**datos_copy)
            objeto.pk = object_id
            objeto.save()
            
            # Marcar como completado
            operacion.marcar_completado()
            return True
            
        except Exception as e:
            operacion.marcar_error(f"Error al crear objeto: {e}")
            logger.error(f"Error al crear objeto {modelo_clase.__name__} con ID {object_id}: {e}", exc_info=True)
            return False

def actualizar_objeto(operacion, modelo_clase, object_id):
    """
    Actualiza un objeto existente según los datos de la operación
    """
    with transaction.atomic():
        try:
            # Intentar obtener el objeto
            try:
                objeto = modelo_clase.objects.get(pk=object_id)
            except modelo_clase.DoesNotExist:
                # El objeto no existe, convertir a creación
                return crear_objeto(operacion, modelo_clase, object_id)
            
            # Obtener datos y actualizar campos
            datos = operacion.datos
            
            # Verificar conflictos si hay un campo de fecha_actualizacion
            if hasattr(objeto, 'fecha_actualizacion') and 'fecha_actualizacion' in datos:
                # Comparar fechas para detectar conflictos
                fecha_actual = getattr(objeto, 'fecha_actualizacion')
                fecha_datos = datos.get('fecha_actualizacion')
                
                if fecha_actual and fecha_datos:
                    # Convertir la fecha de la operación a objeto datetime si es string
                    if isinstance(fecha_datos, str):
                        from django.utils.dateparse import parse_datetime
                        fecha_datos = parse_datetime(fecha_datos)
                    
                    # Si la fecha local es más reciente que la de los datos, puede haber conflicto
                    if fecha_actual > fecha_datos:
                        operacion.marcar_conflicto()
                        return False
            
            # Actualizar campos
            for campo, valor in datos.items():
                if campo != 'id' and hasattr(objeto, campo):
                    setattr(objeto, campo, valor)
            
            objeto.save()
            
            # Marcar como completado
            operacion.marcar_completado()
            return True
            
        except Exception as e:
            operacion.marcar_error(f"Error al actualizar objeto: {e}")
            logger.error(f"Error al actualizar objeto {modelo_clase.__name__} con ID {object_id}: {e}", exc_info=True)
            return False

def eliminar_objeto(operacion, modelo_clase, object_id):
    """
    Elimina un objeto existente según los datos de la operación
    """
    with transaction.atomic():
        try:
            # Intentar obtener y eliminar el objeto
            try:
                objeto = modelo_clase.objects.get(pk=object_id)
                objeto.delete()
            except modelo_clase.DoesNotExist:
                # El objeto ya no existe, considerar como éxito
                pass
            
            # Marcar como completado
            operacion.marcar_completado()
            return True
            
        except Exception as e:
            operacion.marcar_error(f"Error al eliminar objeto: {e}")
            logger.error(f"Error al eliminar objeto {modelo_clase.__name__} con ID {object_id}: {e}", exc_info=True)
            return False

def iniciar_sincronizacion_completa(tienda_id, usuario=None):
    """
    Inicia un proceso de sincronización completa para una tienda
    """
    from tiendas.models import Tienda
    
    try:
        tienda = Tienda.objects.get(pk=tienda_id)
        
        # Crear registro de sincronización
        registro = RegistroSincronizacion.objects.create(
            tienda=tienda,
            fecha_inicio=timezone.now(),
            estado=EstadoSincronizacion.EN_PROCESO,
            iniciado_por=usuario
        )
        
        # Procesar cola de sincronización
        exitosas, fallidas, conflictos = procesar_cola_sincronizacion(
            tienda_id=tienda_id,
            registro_sincronizacion=registro
        )
        
        # Actualizar configuración de sincronización
        try:
            config, created = ConfiguracionSincronizacion.objects.get_or_create(tienda=tienda)
            config.ultima_sincronizacion = timezone.now()
            config.save(update_fields=['ultima_sincronizacion'])
        except Exception as e:
            logger.error(f"Error al actualizar configuración de sincronización: {e}")
        
        return registro.id
    
    except Exception as e:
        logger.error(f"Error al iniciar sincronización completa para tienda {tienda_id}: {e}", exc_info=True)
        return None

def verificar_sincronizaciones_automaticas():
    """
    Verifica y ejecuta sincronizaciones automáticas según la configuración
    """
    ahora = timezone.now()
    
    # Obtener configuraciones con sincronización automática habilitada
    configs = ConfiguracionSincronizacion.objects.filter(sincronizacion_automatica=True)
    
    for config in configs:
        # Verificar si toca sincronizar
        if config.ultima_sincronizacion:
            intervalo = timedelta(minutes=config.intervalo_minutos)
            siguiente_sync = config.ultima_sincronizacion + intervalo
            
            if ahora < siguiente_sync:
                continue  # Aún no es momento de sincronizar
        
        # Iniciar sincronización
        iniciar_sincronizacion_completa(config.tienda.id)

def resolver_conflicto(operacion_id, usar_datos_servidor=True, datos_personalizados=None, usuario=None):
    """
    Resuelve un conflicto de sincronización
    """
    try:
        operacion = ColaSincronizacion.objects.get(pk=operacion_id, tiene_conflicto=True)
        
        if usar_datos_servidor:
            # Usar los datos que ya están en el servidor
            operacion.estado = EstadoSincronizacion.PENDIENTE
            operacion.tiene_conflicto = False
            operacion.resuelto_por = usuario
            operacion.fecha_resolucion = timezone.now()
            operacion.save()
            
            # Volver a procesar
            return procesar_operacion(operacion)
        
        elif datos_personalizados:
            # Usar datos personalizados proporcionados
            operacion.datos = datos_personalizados
            operacion.estado = EstadoSincronizacion.PENDIENTE
            operacion.tiene_conflicto = False
            operacion.resuelto_por = usuario
            operacion.fecha_resolucion = timezone.now()
            operacion.save()
            
            # Volver a procesar
            return procesar_operacion(operacion)
        
        else:
            # Mantener datos locales (no hacer nada con los datos del servidor)
            operacion.estado = EstadoSincronizacion.COMPLETADO
            operacion.tiene_conflicto = False
            operacion.resuelto_por = usuario
            operacion.fecha_resolucion = timezone.now()
            operacion.save()
            return True
    
    except ColaSincronizacion.DoesNotExist:
        logger.error(f"No se encontró la operación de sincronización con ID {operacion_id}")
        return False
    except Exception as e:
        logger.error(f"Error al resolver conflicto {operacion_id}: {e}", exc_info=True)
        return False
