"""
Sistema de notificaciones en tiempo real para el módulo de sincronización.

Este módulo implementa canales de WebSocket para proporcionar actualizaciones
en tiempo real sobre el estado de la sincronización a los clientes conectados.
"""
import json
import logging
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.utils import timezone

logger = logging.getLogger(__name__)

# Grupos de canales para diferentes tipos de notificaciones
CANAL_ESTADO_SINCRONIZACION = 'sync_estado'
CANAL_CONFLICTOS = 'sync_conflictos'
CANAL_COLA = 'sync_cola'

def notificar_conflicto(operacion_id, tienda_id=None, datos=None):
    """
    Notifica a todos los clientes sobre un nuevo conflicto de sincronización
    
    Args:
        operacion_id: ID de la operación con conflicto
        tienda_id: ID de la tienda relacionada con el conflicto (opcional)
        datos: Datos adicionales sobre el conflicto (opcional)
    """
    try:
        from .models import ColaSincronizacion
        
        # Obtener la operación
        operacion = ColaSincronizacion.objects.get(id=operacion_id)
        
        # Preparar datos para envío
        data = {
            'operacion_id': str(operacion.id),
            'modelo': f"{operacion.content_type.app_label}.{operacion.content_type.model}",
            'objeto_id': operacion.object_id,
            'tienda_origen': operacion.tienda_origen.id if operacion.tienda_origen else None,
            'tienda_destino': operacion.tienda_destino.id if operacion.tienda_destino else None,
            'fecha': operacion.fecha_creacion.isoformat(),
            'datos_adicionales': datos or {}
        }
        
        # Obtener el channel layer
        channel_layer = get_channel_layer()
        
        # Enviar a todos los suscriptores del canal de conflictos
        async_to_sync(channel_layer.group_send)(
            CANAL_CONFLICTOS,
            {
                'type': 'update_conflicto',
                'data': data
            }
        )
        
        # Si se especificó una tienda, notificar también a ese canal específico
        if tienda_id:
            tienda_channel = f"{CANAL_ESTADO_SINCRONIZACION}_{tienda_id}"
            async_to_sync(channel_layer.group_send)(
                tienda_channel,
                {
                    'type': 'update_conflicto',
                    'data': data
                }
            )
        
        logger.info(f"Notificación de conflicto enviada para operación {operacion_id}")
        return True
    except Exception as e:
        logger.error(f"Error al notificar conflicto: {e}")
        return False


class SincronizacionConsumer(WebsocketConsumer):
    """
    Consumidor WebSocket para notificaciones de sincronización
    """
    
    def connect(self):
        """
        Establece la conexión WebSocket
        """
        self.user = self.scope['user']
        
        # Solo permitir usuarios autenticados
        if not self.user.is_authenticated:
            self.close()
            return
        
        # Tienda actual (se puede personalizar según contexto)
        tienda_id = self.scope.get('url_route', {}).get('kwargs', {}).get('tienda_id')
        
        # Determinar qué canales suscribir
        self.subscribe_to_channels(tienda_id)
        
        # Aceptar la conexión
        self.accept()
        
        # Enviar estado inicial
        self.send_initial_state(tienda_id)
    
    def subscribe_to_channels(self, tienda_id=None):
        """
        Suscribe al cliente a los canales adecuados
        """
        # Canal principal de estado
        self.grupos = [CANAL_ESTADO_SINCRONIZACION]
        
        # Suscribir al canal general
        async_to_sync(self.channel_layer.group_add)(
            CANAL_ESTADO_SINCRONIZACION,
            self.channel_name
        )
        
        # Si se especificó una tienda, suscribir a ese canal específico
        if tienda_id:
            tienda_channel = f"{CANAL_ESTADO_SINCRONIZACION}_{tienda_id}"
            self.grupos.append(tienda_channel)
            
            async_to_sync(self.channel_layer.group_add)(
                tienda_channel,
                self.channel_name
            )
        
        # Suscribir a canal de conflictos si el usuario puede resolverlos
        if self.user.has_perm('sincronizacion.change_colasincronizacion'):
            self.grupos.append(CANAL_CONFLICTOS)
            
            async_to_sync(self.channel_layer.group_add)(
                CANAL_CONFLICTOS,
                self.channel_name
            )
        
        # Suscribir a canal de cola para administradores
        if self.user.is_staff:
            self.grupos.append(CANAL_COLA)
            
            async_to_sync(self.channel_layer.group_add)(
                CANAL_COLA,
                self.channel_name
            )
    
    def disconnect(self, close_code):
        """
        Maneja la desconexión
        """
        # Desuscribir de todos los grupos
        for grupo in self.grupos:
            async_to_sync(self.channel_layer.group_discard)(
                grupo,
                self.channel_name
            )
    
    def receive(self, text_data):
        """
        Recibe mensajes del cliente
        """
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            # Manejar acciones del cliente
            if action == 'get_status':
                self.send_status_update()
            elif action == 'get_conflicts':
                self.send_conflicts_update()
            elif action == 'get_queue':
                self.send_queue_update()
        except json.JSONDecodeError:
            logger.error("Datos JSON inválidos recibidos")
        except Exception as e:
            logger.error(f"Error al procesar mensaje WebSocket: {e}")
    
    def send_initial_state(self, tienda_id=None):
        """
        Envía el estado inicial al cliente cuando se conecta
        """
        from .models import ColaSincronizacion, ConfiguracionSincronizacion, EstadoSincronizacion
        from tiendas.models import Tienda
        
        try:
            # Determinar tienda
            if tienda_id:
                tienda = Tienda.objects.get(id=tienda_id)
            else:
                tienda = Tienda.objects.filter(activa=True).first()
            
            # Contadores
            pendientes = ColaSincronizacion.objects.filter(
                estado=EstadoSincronizacion.PENDIENTE,
                tienda_origen=tienda
            ).count()
            
            conflictos = ColaSincronizacion.objects.filter(
                tiene_conflicto=True,
                tienda_origen=tienda
            ).count()
            
            # Configuración
            try:
                config = ConfiguracionSincronizacion.objects.get(tienda=tienda)
                config_data = {
                    'sincronizacion_automatica': config.sincronizacion_automatica,
                    'intervalo_minutos': config.intervalo_minutos,
                    'ultima_sincronizacion': config.ultima_sincronizacion.isoformat() if config.ultima_sincronizacion else None
                }
            except ConfiguracionSincronizacion.DoesNotExist:
                config_data = {
                    'sincronizacion_automatica': True,
                    'intervalo_minutos': 15,
                    'ultima_sincronizacion': None
                }
            
            # Enviar estado inicial
            self.send(text_data=json.dumps({
                'type': 'initial_state',
                'pendientes': pendientes,
                'conflictos': conflictos,
                'config': config_data,
                'tienda': {
                    'id': tienda.id,
                    'nombre': tienda.nombre,
                    'es_central': tienda.es_central
                } if tienda else None,
                'timestamp': timezone.now().isoformat()
            }))
        
        except Exception as e:
            logger.error(f"Error al enviar estado inicial: {e}")
            self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error al obtener estado inicial'
            }))
    
    def update_estado(self, event):
        """
        Recibe actualización de estado y la reenvía al cliente
        """
        # Reenviar al cliente
        self.send(text_data=json.dumps({
            'type': 'status_update',
            'data': event['data']
        }))
    
    def update_conflicto(self, event):
        """
        Recibe actualización de conflicto y la reenvía al cliente
        """
        self.send(text_data=json.dumps({
            'type': 'conflict_update',
            'data': event['data']
        }))
    
    def update_cola(self, event):
        """
        Recibe actualización de cola y la reenvía al cliente
        """
        self.send(text_data=json.dumps({
            'type': 'queue_update',
            'data': event['data']
        }))


def notificar_cambio_estado(tienda_id=None, data=None):
    """
    Notifica a los clientes conectados sobre un cambio en el estado de sincronización
    """
    try:
        channel_layer = get_channel_layer()
        
        if data is None:
            from .models import ColaSincronizacion, EstadoSincronizacion
            
            # Preparar datos básicos si no se proporcionaron
            pendientes = ColaSincronizacion.objects.filter(
                estado=EstadoSincronizacion.PENDIENTE
            )
            
            if tienda_id:
                pendientes = pendientes.filter(tienda_origen_id=tienda_id)
            
            data = {
                'pendientes': pendientes.count(),
                'timestamp': timezone.now().isoformat()
            }
        
        # Enviar a canal general
        async_to_sync(channel_layer.group_send)(
            CANAL_ESTADO_SINCRONIZACION,
            {
                'type': 'update_estado',
                'data': data
            }
        )
        
        # Si se especificó tienda, enviar a su canal específico
        if tienda_id:
            tienda_channel = f"{CANAL_ESTADO_SINCRONIZACION}_{tienda_id}"
            async_to_sync(channel_layer.group_send)(
                tienda_channel,
                {
                    'type': 'update_estado',
                    'data': data
                }
            )
    
    except Exception as e:
        logger.error(f"Error al notificar cambio de estado: {e}")


def notificar_nuevo_conflicto(operacion):
    """
    Notifica a los clientes sobre un nuevo conflicto
    """
    try:
        from .serializers import ColaSincronizacionSerializer
        
        channel_layer = get_channel_layer()
        
        # Serializar operación
        serializer = ColaSincronizacionSerializer(operacion)
        
        # Enviar notificación
        async_to_sync(channel_layer.group_send)(
            CANAL_CONFLICTOS,
            {
                'type': 'update_conflicto',
                'data': {
                    'operacion': serializer.data,
                    'mensaje': f"Nuevo conflicto detectado en {operacion.content_type}",
                    'timestamp': timezone.now().isoformat()
                }
            }
        )
    
    except Exception as e:
        logger.error(f"Error al notificar nuevo conflicto: {e}")


def notificar_actualizacion_cola(tienda_id=None, resumen=None):
    """
    Notifica a los clientes sobre cambios en la cola de sincronización
    """
    try:
        channel_layer = get_channel_layer()
        
        if resumen is None:
            from .models import ColaSincronizacion, EstadoSincronizacion
            from django.db.models import Count
            
            # Obtener resumen por estado
            queryset = ColaSincronizacion.objects.values('estado').annotate(total=Count('id'))
            
            if tienda_id:
                queryset = queryset.filter(tienda_origen_id=tienda_id)
            
            resumen = {estado['estado']: estado['total'] for estado in queryset}
        
        # Añadir timestamp
        data = {
            'resumen': resumen,
            'timestamp': timezone.now().isoformat()
        }
        
        # Enviar notificación
        async_to_sync(channel_layer.group_send)(
            CANAL_COLA,
            {
                'type': 'update_cola',
                'data': data
            }
        )
    
    except Exception as e:
        logger.error(f"Error al notificar actualización de cola: {e}")
