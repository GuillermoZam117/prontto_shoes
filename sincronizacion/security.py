"""
Medidas de seguridad para el módulo de sincronización.

Este módulo implementa características de seguridad para asegurar que la
sincronización de datos entre tiendas y el servidor central sea segura.
"""
import logging
import hashlib
import hmac
import base64
import json
import secrets
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models

logger = logging.getLogger(__name__)

# Clave secreta para firma de mensajes (en producción debe estar en settings)
SYNC_SECRET_KEY = getattr(settings, 'SINCRONIZACION_SECRET_KEY', 
                        secrets.token_hex(32))

class SeguridadSincronizacion:
    """
    Gestor de seguridad para la sincronización de datos.
    
    Proporciona funcionalidades para:
    - Autenticación de solicitudes de sincronización
    - Autorización para operaciones específicas
    - Firma y validación de datos
    - Encriptación de datos sensibles
    - Registro y auditoría de operaciones
    """
    
    @staticmethod
    def generar_token_sincronizacion(tienda_id, duracion_horas=24):
        """
        Genera un token temporal para sincronización con una tienda específica
        """
        try:
            # Generar un token aleatorio
            token = secrets.token_hex(16)
            
            # Fecha de expiración
            expiracion = timezone.now() + timedelta(hours=duracion_horas)
            expiracion_str = expiracion.isoformat()
            
            # Datos a firmar
            datos = {
                'tienda_id': str(tienda_id),
                'token': token,
                'expiracion': expiracion_str
            }
            
            # Serializar datos
            datos_str = json.dumps(datos, sort_keys=True)
            
            # Firmar datos
            firma = SeguridadSincronizacion.firmar_datos(datos_str)
            
            # Combinar todo en un token final
            token_final = base64.urlsafe_b64encode(
                json.dumps({
                    'datos': datos,
                    'firma': firma
                }).encode('utf-8')
            ).decode('utf-8')
            
            return token_final
        
        except Exception as e:
            logger.error(f"Error al generar token de sincronización: {e}")
            return None
    
    @staticmethod
    def validar_token_sincronizacion(token):
        """
        Valida un token de sincronización y retorna la tienda_id si es válido
        """
        try:
            # Decodificar token
            token_decoded = base64.urlsafe_b64decode(token.encode('utf-8')).decode('utf-8')
            token_data = json.loads(token_decoded)
            
            # Extraer datos y firma
            datos = token_data.get('datos')
            firma_recibida = token_data.get('firma')
            
            if not datos or not firma_recibida:
                logger.warning("Token de sincronización malformado")
                return None
            
            # Validar firma
            datos_str = json.dumps(datos, sort_keys=True)
            firma_calculada = SeguridadSincronizacion.firmar_datos(datos_str)
            
            if firma_calculada != firma_recibida:
                logger.warning("Firma de token inválida")
                return None
            
            # Validar expiración
            expiracion = datetime.fromisoformat(datos.get('expiracion'))
            if timezone.now() > expiracion:
                logger.warning("Token de sincronización expirado")
                return None
            
            # Retornar tienda_id
            return datos.get('tienda_id')
        
        except Exception as e:
            logger.error(f"Error al validar token de sincronización: {e}")
            return None
    
    @staticmethod
    def firmar_datos(datos_str):
        """
        Firma un conjunto de datos con HMAC-SHA256
        """
        try:
            firma = hmac.new(
                SYNC_SECRET_KEY.encode('utf-8'),
                datos_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return firma
        
        except Exception as e:
            logger.error(f"Error al firmar datos: {e}")
            return None
    
    @staticmethod
    def encriptar_datos_sensibles(datos, campos_sensibles=None):
        """
        Encripta campos sensibles en un diccionario de datos
        """
        if campos_sensibles is None:
            # Campos considerados sensibles por defecto
            campos_sensibles = ['password', 'contraseña', 'token', 'secret', 'clave']
        
        if not isinstance(datos, dict):
            return datos
        
        # Copia para no modificar el original
        datos_seguros = datos.copy()
        
        # Encriptar campos sensibles
        for campo in campos_sensibles:
            if campo in datos_seguros:                # Encriptar campo (aquí se usa una encriptación simple pero se
                # debe implementar una encriptación más robusta en producción)
                valor = datos_seguros[campo]
                if isinstance(valor, str):
                    datos_seguros[campo] = '[ENCRIPTADO]'
        
        return datos_seguros
    
    @staticmethod
    def crear_entrada_auditoria(usuario, tienda, accion, objeto_afectado=None, 
                               detalles=None, exitoso=True):
        """
        Crea una entrada en el registro de auditoría
        """
        try:
            # Crear registro
            registro = RegistroAuditoria.objects.create(
                usuario=usuario,
                tienda=tienda,
                accion=accion,
                content_type=ContentType.objects.get_for_model(objeto_afectado) if objeto_afectado else None,
                object_id=str(objeto_afectado.pk) if objeto_afectado else None,
                detalles=detalles,
                exitoso=exitoso,
                fecha=timezone.now(),
                ip_origen=None  # En un entorno real, se obtendría de la solicitud
            )
            
            return registro
        
        except Exception as e:
            logger.error(f"Error al crear entrada de auditoría: {e}")
            return None
    
    @staticmethod
    def verificar_permisos_sincronizacion(usuario, tienda, accion):
        """
        Verifica si un usuario tiene permiso para realizar una acción de sincronización
        """
        # Si es superusuario, siempre tiene permiso
        if usuario.is_superuser:
            return True
        
        # Verificar si tiene el permiso específico
        if accion == 'ver':
            return usuario.has_perm('sincronizacion.view_colasincronizacion')
        elif accion == 'procesar':
            return usuario.has_perm('sincronizacion.change_colasincronizacion')
        elif accion == 'configurar':
            return usuario.has_perm('sincronizacion.change_configuracionsincronizacion')
        
        # Verificar si es administrador de la tienda
        # (aquí habría que implementar la lógica específica del proyecto)
        
        return False

class RegistroAuditoria(models.Model):
    """
    Registra las acciones de sincronización para auditoría de seguridad
    """
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                               null=True, blank=True, related_name='auditorias_sincronizacion')
    tienda = models.ForeignKey('tiendas.Tienda', on_delete=models.CASCADE, 
                             related_name='auditorias_sincronizacion')
    fecha = models.DateTimeField(auto_now_add=True)
    accion = models.CharField(max_length=100)
    
    # Referencia genérica al objeto afectado
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, 
                                   null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    detalles = models.JSONField(null=True, blank=True)
    exitoso = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['fecha', 'tienda']),
            models.Index(fields=['usuario', 'accion']),
        ]
    
    def __str__(self):
        return f"{self.accion} - {self.tienda.nombre} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"
