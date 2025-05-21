from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from django.conf import settings
import inspect
import logging

from .models import ColaSincronizacion, TipoOperacion, ConfiguracionSincronizacion
from tiendas.models import Tienda

logger = logging.getLogger(__name__)

# Lista de modelos que deben sincronizarse
# Formato: {'app_label.model_name': {'excluded_fields': ['field1', 'field2'], 'conditions': callable}}
MODELOS_SINCRONIZABLES = {
    'productos.Producto': {'excluded_fields': ['imagen', 'fecha_actualizacion']},
    'productos.Catalogo': {'excluded_fields': []},
    'clientes.Cliente': {'excluded_fields': ['foto']},
    'ventas.Pedido': {'excluded_fields': []},
    'ventas.DetallePedido': {'excluded_fields': []},
    'inventario.Inventario': {'excluded_fields': []},
    'inventario.Traspaso': {'excluded_fields': []},
    'inventario.TraspasoItem': {'excluded_fields': []},
    'devoluciones.Devolucion': {'excluded_fields': []},
    'descuentos.TabuladorDescuento': {'excluded_fields': []},
    'descuentos.DescuentoCliente': {'excluded_fields': []},
    'proveedores.Proveedor': {'excluded_fields': []},
    'requisiciones.Requisicion': {'excluded_fields': []},
    'requisiciones.DetalleRequisicion': {'excluded_fields': []},
}

def serializar_instancia(instance, excluded_fields=None):
    """
    Serializa una instancia de modelo a un diccionario
    Excluye los campos especificados y maneja relaciones básicas
    """
    if excluded_fields is None:
        excluded_fields = []
    
    datos = {}
    for field in instance._meta.fields:
        if field.name in excluded_fields:
            continue
        
        value = getattr(instance, field.name)
        
        # Manejar tipos de datos especiales
        if hasattr(value, 'isoformat'):  # Fechas y horas
            datos[field.name] = value.isoformat()
        elif hasattr(value, 'pk'):  # Relaciones
            datos[field.name] = value.pk
        else:
            datos[field.name] = value
    
    return datos

def es_modelo_sincronizable(instance):
    """Determina si un modelo debe incluirse en la sincronización"""
    modelo_str = f"{instance._meta.app_label}.{instance._meta.model_name}"
    return modelo_str in MODELOS_SINCRONIZABLES

def obtener_config_modelo(instance):
    """Obtiene la configuración de sincronización para un modelo"""
    modelo_str = f"{instance._meta.app_label}.{instance._meta.model_name}"
    return MODELOS_SINCRONIZABLES.get(modelo_str, {'excluded_fields': []})

def obtener_tienda_actual():
    """
    Obtiene la tienda actual basada en la configuración
    En un entorno real, esto podría obtenerse del contexto de la solicitud
    o de una configuración global
    """
    try:
        # Para efectos de demostración, usar la primera tienda como tienda actual
        return Tienda.objects.filter(activa=True).first()
    except Exception as e:
        logger.error(f"Error al obtener la tienda actual: {e}")
        return None

def crear_operacion_sincronizacion(instance, tipo_operacion, tienda=None):
    """
    Crea una entrada en la cola de sincronización para la instancia dada
    """
    if not es_modelo_sincronizable(instance):
        return None
    
    if not tienda:
        tienda = obtener_tienda_actual()
        if not tienda:
            logger.error(f"No se pudo determinar la tienda para sincronizar {instance}")
            return None
    
    try:
        # Obtener configuración para el modelo
        config_modelo = obtener_config_modelo(instance)
        excluded_fields = config_modelo.get('excluded_fields', [])
        
        # Serializar la instancia
        datos_serializados = serializar_instancia(instance, excluded_fields)
        
        # Obtener el content type
        content_type = ContentType.objects.get_for_model(instance)
        
        # Obtener tienda central o servidor
        tienda_central = Tienda.objects.filter(es_central=True).first()
        
        # Crear la operación de sincronización
        operacion = ColaSincronizacion.objects.create(
            tienda_origen=tienda,
            tienda_destino=tienda_central,  # Si es None, indica servidor central
            content_type=content_type,
            object_id=str(instance.pk),
            tipo_operacion=tipo_operacion,
            datos=datos_serializados,
        )
        
        # Establecer prioridad según configuración
        try:
            config_sync = ConfiguracionSincronizacion.objects.get(tienda=tienda)
            operacion.prioridad = config_sync.obtener_prioridad(instance.__class__)
            operacion.save(update_fields=['prioridad'])
        except ConfiguracionSincronizacion.DoesNotExist:
            pass
        
        logger.info(f"Creada operación de sincronización: {operacion}")
        return operacion
        
    except Exception as e:
        logger.error(f"Error al crear operación de sincronización para {instance}: {e}")
        return None

@receiver(post_save)
def on_model_save(sender, instance, created, **kwargs):
    """
    Detecta cuando un modelo es creado o actualizado y lo añade a la cola de sincronización
    """
    # Evitar recursión infinita al guardar la propia ColaSincronizacion
    if sender == ColaSincronizacion or sender == ConfiguracionSincronizacion:
        return
    
    # Evitar procesar modelos no sincronizables
    if not es_modelo_sincronizable(instance):
        return
    
    # Determinar tipo de operación
    tipo_operacion = TipoOperacion.CREAR if created else TipoOperacion.ACTUALIZAR
    
    # Crear operación de sincronización
    crear_operacion_sincronizacion(instance, tipo_operacion)

@receiver(post_delete)
def on_model_delete(sender, instance, **kwargs):
    """
    Detecta cuando un modelo es eliminado y lo añade a la cola de sincronización
    """
    # Evitar recursión infinita
    if sender == ColaSincronizacion or sender == ConfiguracionSincronizacion:
        return
    
    # Evitar procesar modelos no sincronizables
    if not es_modelo_sincronizable(instance):
        return
    
    # Crear operación de sincronización para eliminación
    crear_operacion_sincronizacion(instance, TipoOperacion.ELIMINAR)
