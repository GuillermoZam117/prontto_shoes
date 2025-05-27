from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.utils import timezone

User = get_user_model()

class LogAuditoria(models.Model):
    ACCION_CHOICES = [
        ('CREATE', 'Crear'),
        ('UPDATE', 'Actualizar'), 
        ('DELETE', 'Eliminar'),
        ('LOGIN', 'Iniciar Sesión'),
        ('LOGOUT', 'Cerrar Sesión'),
        ('BACKUP', 'Respaldo'),
        ('EXPORT', 'Exportar'),
        ('IMPORT', 'Importar'),
        ('CONFIG', 'Configuración'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=20, choices=ACCION_CHOICES)
    descripcion = models.TextField(blank=True)
    modelo_afectado = models.CharField(max_length=100, blank=True)
    objeto_id = models.CharField(max_length=50, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'

    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else 'Sistema'
        return f"{self.fecha.strftime('%Y-%m-%d %H:%M')} - {usuario_str}: {self.get_accion_display()}"

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefono = models.CharField(max_length=15, blank=True)
    tienda_asignada = models.ForeignKey('tiendas.Tienda', on_delete=models.SET_NULL, null=True, blank=True)
    fecha_ultimo_acceso = models.DateTimeField(null=True, blank=True)
    intentos_login_fallidos = models.IntegerField(default=0)
    cuenta_bloqueada = models.BooleanField(default=False)
    fecha_bloqueo = models.DateTimeField(null=True, blank=True)
    requiere_cambio_password = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
    
    def __str__(self):
        return f"Perfil de {self.usuario.username}"

class ConfiguracionSistema(models.Model):
    clave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()
    descripcion = models.TextField(blank=True)
    tipo_dato = models.CharField(max_length=20, choices=[
        ('string', 'Texto'),
        ('integer', 'Número Entero'),
        ('float', 'Número Decimal'),
        ('boolean', 'Verdadero/Falso'),
        ('json', 'JSON'),
    ], default='string')
    fecha_modificacion = models.DateTimeField(auto_now=True)
    modificado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuraciones del Sistema'
    
    def __str__(self):
        return f"{self.clave}: {self.valor[:50]}"
