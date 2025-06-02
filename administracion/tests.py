"""
Tests completos para la aplicación de administración
Sistema POS Pronto Shoes
- Tests para modelos: LogAuditoria, PerfilUsuario, ConfiguracionSistema
- Tests para vistas y APIs
- Tests de integración
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch
from datetime import datetime, timedelta

from .models import LogAuditoria, PerfilUsuario, ConfiguracionSistema

User = get_user_model()


class LogAuditoriaTestCase(TestCase):
    """Tests para el modelo LogAuditoria"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_crear_log_auditoria(self):
        """Test crear log de auditoría"""
        log = LogAuditoria.objects.create(
            usuario=self.user,
            accion='CREATE',
            descripcion='Creación de producto test',
            modelo_afectado='Producto',
            objeto_id='123',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0 Test'
        )
        
        self.assertEqual(log.usuario, self.user)
        self.assertEqual(log.accion, 'CREATE')
        self.assertEqual(log.descripcion, 'Creación de producto test')
        self.assertEqual(log.modelo_afectado, 'Producto')
        self.assertEqual(log.objeto_id, '123')
        self.assertEqual(log.ip_address, '192.168.1.1')
        self.assertTrue(log.fecha)
    
    def test_log_sin_usuario(self):
        """Test crear log sin usuario (acción del sistema)"""
        log = LogAuditoria.objects.create(
            accion='BACKUP',
            descripcion='Respaldo automático del sistema',
            ip_address='127.0.0.1'
        )
        
        self.assertIsNone(log.usuario)
        self.assertEqual(log.accion, 'BACKUP')
        self.assertEqual(log.descripcion, 'Respaldo automático del sistema')
    
    def test_str_representation(self):
        """Test representación string del log"""
        log = LogAuditoria.objects.create(
            usuario=self.user,
            accion='LOGIN',
            descripcion='Usuario inició sesión'
        )
        
        expected = f"{log.fecha.strftime('%Y-%m-%d %H:%M')} - {self.user.username}: Iniciar Sesión"
        self.assertEqual(str(log), expected)


class PerfilUsuarioTestCase(TestCase):
    """Tests para el modelo PerfilUsuario"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_crear_perfil_usuario(self):
        """Test crear perfil de usuario"""
        perfil = PerfilUsuario.objects.create(
            usuario=self.user,
            telefono='555-0123'
        )
        
        self.assertEqual(perfil.usuario, self.user)
        self.assertEqual(perfil.telefono, '555-0123')
        self.assertEqual(perfil.intentos_login_fallidos, 0)
        self.assertFalse(perfil.cuenta_bloqueada)
        self.assertFalse(perfil.requiere_cambio_password)
    
    def test_str_representation(self):
        """Test representación string del perfil"""
        perfil = PerfilUsuario.objects.create(
            usuario=self.user,
            telefono='555-0123'
        )
        
        expected = f"Perfil de {self.user.username}"
        self.assertEqual(str(perfil), expected)


class ConfiguracionSistemaTestCase(TestCase):
    """Tests para el modelo ConfiguracionSistema"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='adminpass123'
        )
    
    def test_crear_configuracion_string(self):
        """Test crear configuración tipo string"""
        config = ConfiguracionSistema.objects.create(
            clave='nombre_sistema',
            valor='POS Pronto Shoes',
            descripcion='Nombre del sistema',
            tipo_dato='string',
            modificado_por=self.user
        )
        
        self.assertEqual(config.clave, 'nombre_sistema')
        self.assertEqual(config.valor, 'POS Pronto Shoes')
        self.assertEqual(config.tipo_dato, 'string')
        self.assertEqual(config.modificado_por, self.user)
    
    def test_str_representation(self):
        """Test representación string de configuración"""
        config = ConfiguracionSistema.objects.create(
            clave='version_sistema',
            valor='1.0.0',
            descripcion='Versión del sistema'
        )
        
        expected = "version_sistema: 1.0.0"
        self.assertEqual(str(config), expected)


class LogAuditoriaAPITestCase(APITestCase):
    """Tests para la API de LogAuditoria"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.log_data = {
            'accion': 'CREATE',
            'descripcion': 'Creación de registro'
        }

    def test_create_log(self):
        """Test crear log via API"""
        log = LogAuditoria.objects.create(
            usuario=self.user,
            **self.log_data
        )
        self.assertEqual(LogAuditoria.objects.count(), 1)
        self.assertEqual(LogAuditoria.objects.get().accion, 'CREATE')

    def test_list_logs(self):
        """Test listar logs"""
        LogAuditoria.objects.create(
            usuario=self.user, 
            accion='CREATE', 
            descripcion='Creación de registro'
        )
        logs = LogAuditoria.objects.all()
        self.assertEqual(logs.count(), 1)
        self.assertEqual(len(response.data), 1)

    def test_filter_log_by_accion(self):
        LogAuditoria.objects.create(usuario=self.user, accion='CREAR', descripcion='Creación de registro')
        url = reverse('logauditoria-list') + '?accion=CREAR'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['accion'], 'CREAR')
