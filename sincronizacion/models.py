from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from tiendas.models import Tienda
from django.conf import settings
import uuid
import json

# Importamos el modelo de auditoría de seguridad
from .security import RegistroAuditoria

class EstadoSincronizacion(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    EN_PROCESO = 'en_proceso', 'En Proceso'
    COMPLETADO = 'completado', 'Completado'
    ERROR = 'error', 'Error'
    CONFLICTO = 'conflicto', 'Conflicto'

class TipoOperacion(models.TextChoices):
    CREAR = 'crear', 'Crear'
    ACTUALIZAR = 'actualizar', 'Actualizar'
    ELIMINAR = 'eliminar', 'Eliminar'

class ColaSincronizacion(models.Model):
    """
    Representa una operación pendiente de sincronización entre tiendas o
    entre una tienda y el servidor central.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tienda_origen = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name='operaciones_salientes')
    tienda_destino = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name='operaciones_entrantes',
                                     null=True, blank=True, help_text='Tienda destino (nulo si es servidor central)')
    
    # Referencia genérica al objeto a sincronizar
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)  # Usamos CharField en lugar de PositiveIntegerField para soportar UUIDs
    content_object = GenericForeignKey('content_type', 'object_id')
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    tipo_operacion = models.CharField(max_length=20, choices=TipoOperacion.choices)
    estado = models.CharField(max_length=20, choices=EstadoSincronizacion.choices, default=EstadoSincronizacion.PENDIENTE)
    intentos = models.PositiveSmallIntegerField(default=0)
    prioridad = models.PositiveSmallIntegerField(default=1, help_text='Menor número = mayor prioridad')
    
    # Almacenar los datos para sincronizar como JSON
    datos = models.JSONField(help_text='Datos serializados del objeto para sincronizar')
    
    # Metadatos para solución de conflictos
    tiene_conflicto = models.BooleanField(default=False)
    datos_servidor = models.JSONField(null=True, blank=True, help_text='Datos del servidor en caso de conflicto')
    diferencias = models.JSONField(null=True, blank=True, help_text='Diferencias detectadas en conflicto')
    resuelto_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='conflictos_resueltos')
    fecha_resolucion = models.DateTimeField(null=True, blank=True)
    
    # Error en caso de problemas
    error_mensaje = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Operación de Sincronización"
        verbose_name_plural = "Cola de Sincronización"
        ordering = ['prioridad', 'fecha_creacion']
        indexes = [
            models.Index(fields=['estado', 'tienda_origen']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_operacion_display()} - {self.content_type} - {self.estado}"
    
    def marcar_en_proceso(self):
        self.estado = EstadoSincronizacion.EN_PROCESO
        self.save(update_fields=['estado', 'fecha_actualizacion'])
    
    def marcar_completado(self):
        self.estado = EstadoSincronizacion.COMPLETADO
        self.save(update_fields=['estado', 'fecha_actualizacion'])
    
    def marcar_error(self, mensaje):
        self.estado = EstadoSincronizacion.ERROR
        self.error_mensaje = mensaje
        self.intentos += 1
        self.save(update_fields=['estado', 'error_mensaje', 'intentos', 'fecha_actualizacion'])
    
    def marcar_conflicto(self):
        self.estado = EstadoSincronizacion.CONFLICTO
        self.tiene_conflicto = True
        self.save(update_fields=['estado', 'tiene_conflicto', 'fecha_actualizacion'])
    
    def resolver_conflicto(self, usuario, datos_resueltos=None):
        self.tiene_conflicto = False
        self.resuelto_por = usuario
        self.fecha_resolucion = timezone.now()
        if datos_resueltos:
            self.datos = datos_resueltos
        self.save()


class ConfiguracionSincronizacion(models.Model):
    """
    Configuración del comportamiento de sincronización para cada tienda.
    """
    tienda = models.OneToOneField(Tienda, on_delete=models.CASCADE, related_name='configuracion_sincronizacion')
    sincronizacion_automatica = models.BooleanField(default=True)
    intervalo_minutos = models.PositiveIntegerField(default=15)
    ultima_sincronizacion = models.DateTimeField(null=True, blank=True)
    
    # Prioridades por modelo
    prioridades = models.JSONField(default=dict, help_text='Prioridades por modelo en formato {"app.Modelo": 1}')
    
    # Estrategia de resolución de conflictos por modelo
    estrategias_conflicto = models.JSONField(
        default=dict, 
        help_text='Estrategias por modelo en formato {"app.Modelo": "central"} o {"app.Modelo": "local"}'
    )
    
    class Meta:
        verbose_name = "Configuración de Sincronización"
        verbose_name_plural = "Configuraciones de Sincronización"
    
    def __str__(self):
        return f"Configuración de sincronización para {self.tienda.nombre}"
    
    def obtener_prioridad(self, modelo):
        """Obtiene la prioridad para un modelo específico"""
        modelo_str = f"{modelo._meta.app_label}.{modelo._meta.model_name}"
        return self.prioridades.get(modelo_str, 10)  # Default prioridad 10 (baja)
    
    def obtener_estrategia_conflicto(self, modelo):
        """Obtiene la estrategia de resolución de conflictos para un modelo"""
        modelo_str = f"{modelo._meta.app_label}.{modelo._meta.model_name}"
        return self.estrategias_conflicto.get(modelo_str, "central")  # Default: central gana


class RegistroSincronizacion(models.Model):
    """
    Registro histórico de sincronizaciones realizadas.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tienda = models.ForeignKey(Tienda, on_delete=models.CASCADE, related_name='historial_sincronizacion')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    
    operaciones_totales = models.PositiveIntegerField(default=0)
    operaciones_exitosas = models.PositiveIntegerField(default=0)
    operaciones_fallidas = models.PositiveIntegerField(default=0)
    operaciones_con_conflicto = models.PositiveIntegerField(default=0)
    
    resumen = models.JSONField(default=dict, help_text='Resumen por modelo y operación')
    estado = models.CharField(max_length=20, choices=EstadoSincronizacion.choices, default=EstadoSincronizacion.EN_PROCESO)
    iniciado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Registro de Sincronización"
        verbose_name_plural = "Historial de Sincronización"
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f"Sincronización {self.tienda.nombre} - {self.fecha_inicio.strftime('%d/%m/%Y %H:%M')}"
    
    def finalizar(self, exitosas, fallidas, conflictos):
        self.fecha_fin = timezone.now()
        self.operaciones_exitosas = exitosas
        self.operaciones_fallidas = fallidas
        self.operaciones_con_conflicto = conflictos
        self.operaciones_totales = exitosas + fallidas + conflictos
        self.estado = EstadoSincronizacion.COMPLETADO
        self.save()
    
    def calcular_duracion(self):
        if self.fecha_fin:
            return (self.fecha_fin - self.fecha_inicio).total_seconds() / 60  # Duración en minutos
        return None
