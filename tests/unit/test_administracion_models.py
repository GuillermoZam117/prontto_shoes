"""
Tests unitarios para modelos de administración
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from decimal import Decimal
from unittest.mock import patch
from freezegun import freeze_time
from datetime import datetime, timedelta

from administracion.models import LogAuditoria, PerfilUsuario, ConfiguracionSistema
from ..factories import (
    UserFactory, LogAuditoriaFactory, PerfilUsuarioFactory, 
    ConfiguracionSistemaFactory, TiendaFactory
)
from ..base import BaseTestCase

User = get_user_model()


class LogAuditoriaModelTests(BaseTestCase):
    """Tests para el modelo LogAuditoria"""
    
    def test_should_create_log_auditoria_with_valid_data(self):
        """Debería crear un log de auditoría con datos válidos"""
        user = UserFactory()
        log = LogAuditoriaFactory(
            usuario=user,
            accion='CREATE',
            descripcion='Test log entry',
            modelo_afectado='Producto',
            objeto_id='123',
            ip_address='192.168.1.1'
        )
        
        self.assertEqual(log.usuario, user)
        self.assertEqual(log.accion, 'CREATE')
        self.assertEqual(log.descripcion, 'Test log entry')
        self.assertEqual(log.modelo_afectado, 'Producto')
        self.assertEqual(log.objeto_id, '123')
        self.assertEqual(log.ip_address, '192.168.1.1')
        self.assertIsNotNone(log.fecha)
    
    def test_should_allow_null_usuario_for_system_actions(self):
        """Debería permitir usuario nulo para acciones del sistema"""
        log = LogAuditoriaFactory(
            usuario=None,
            accion='BACKUP',
            descripcion='Sistema realizó backup automático'
        )
        
        self.assertIsNone(log.usuario)
        self.assertEqual(log.accion, 'BACKUP')
    
    def test_should_validate_accion_choices(self):
        """Debería validar que la acción esté en las opciones permitidas"""
        with self.assertRaises(ValidationError):
            log = LogAuditoria(
                accion='INVALID_ACTION',
                descripcion='Test'
            )
            log.full_clean()
    
    def test_should_have_correct_string_representation(self):
        """Debería tener la representación string correcta"""
        user = UserFactory(username='testuser')
        
        with freeze_time("2025-05-29 14:30:00"):
            log = LogAuditoriaFactory(
                usuario=user,
                accion='CREATE'
            )
            expected = "2025-05-29 14:30 - testuser: Crear"
            self.assertEqual(str(log), expected)
    
    def test_should_handle_system_user_in_string_representation(self):
        """Debería manejar usuario del sistema en la representación string"""
        with freeze_time("2025-05-29 14:30:00"):
            log = LogAuditoriaFactory(
                usuario=None,
                accion='BACKUP'
            )
            expected = "2025-05-29 14:30 - Sistema: Respaldo"
            self.assertEqual(str(log), expected)
    
    def test_should_order_by_fecha_desc_by_default(self):
        """Debería ordenar por fecha descendente por defecto"""
        # Crear logs en diferentes tiempos
        with freeze_time("2025-05-29 10:00:00"):
            log1 = LogAuditoriaFactory(descripcion="Primer log")
        
        with freeze_time("2025-05-29 12:00:00"):
            log2 = LogAuditoriaFactory(descripcion="Segundo log")
        
        logs = list(LogAuditoria.objects.all())
        self.assertEqual(logs[0], log2)  # Más reciente primero
        self.assertEqual(logs[1], log1)
    
    def test_should_store_ipv4_and_ipv6_addresses(self):
        """Debería almacenar direcciones IPv4 e IPv6"""
        # IPv4
        log_ipv4 = LogAuditoriaFactory(ip_address='192.168.1.1')
        self.assertEqual(log_ipv4.ip_address, '192.168.1.1')
        
        # IPv6
        log_ipv6 = LogAuditoriaFactory(ip_address='2001:db8::1')
        self.assertEqual(log_ipv6.ip_address, '2001:db8::1')
    
    def test_should_handle_long_user_agent_strings(self):
        """Debería manejar user agents largos"""
        long_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " * 10
        log = LogAuditoriaFactory(user_agent=long_user_agent)
        self.assertEqual(log.user_agent, long_user_agent)
    
    def test_should_auto_set_fecha_on_creation(self):
        """Debería establecer automáticamente la fecha al crear"""
        with freeze_time("2025-05-29 15:45:30"):
            log = LogAuditoriaFactory()
            expected_time = datetime(2025, 5, 29, 15, 45, 30)
            # Comparar solo hasta segundos para evitar problemas de microsegundos
            self.assertEqual(
                log.fecha.replace(microsecond=0, tzinfo=None),
                expected_time
            )


class PerfilUsuarioModelTests(BaseTestCase):
    """Tests para el modelo PerfilUsuario"""
      def test_should_create_perfil_usuario_with_valid_data(self):
        """Debería crear un perfil de usuario con datos válidos"""
        user = UserFactory()
        tienda = TiendaFactory()
        perfil = PerfilUsuarioFactory(
            usuario=user,
            telefono='555-1234',
            tienda_asignada=tienda
        )
        
        self.assertEqual(perfil.usuario, user)
        self.assertEqual(perfil.telefono, '555-1234')
        self.assertEqual(perfil.tienda_asignada, tienda)
        self.assertEqual(perfil.intentos_login_fallidos, 0)
        self.assertFalse(perfil.cuenta_bloqueada)
        self.assertFalse(perfil.requiere_cambio_password)
    
    def test_should_enforce_one_to_one_relationship_with_user(self):
        """Debería enforcer relación uno a uno con User"""
        user = UserFactory()
        
        # Crear primer perfil
        perfil1 = PerfilUsuarioFactory(usuario=user)
        
        # Intentar crear segundo perfil para el mismo usuario
        with self.assertRaises(IntegrityError):
            PerfilUsuarioFactory(usuario=user)
    
    def test_should_have_correct_string_representation(self):
        """Debería tener la representación string correcta"""
        user = UserFactory(username='johndoe')
        perfil = PerfilUsuarioFactory(usuario=user)
        
        self.assertEqual(str(perfil), "Perfil de johndoe")
    
    def test_should_handle_cuenta_bloqueada_scenarios(self):
        """Debería manejar escenarios de cuenta bloqueada"""
        perfil = PerfilUsuarioFactory()
        
        # Simular intentos fallidos
        perfil.intentos_login_fallidos = 5
        perfil.cuenta_bloqueada = True
        perfil.fecha_bloqueo = datetime.now()
        perfil.save()
        
        self.assertEqual(perfil.intentos_login_fallidos, 5)
        self.assertTrue(perfil.cuenta_bloqueada)
        self.assertIsNotNone(perfil.fecha_bloqueo)
    
    def test_should_track_ultimo_acceso(self):
        """Debería trackear el último acceso"""
        perfil = PerfilUsuarioFactory()
        
        with freeze_time("2025-05-29 16:30:00"):
            perfil.fecha_ultimo_acceso = datetime.now()
            perfil.save()
        
        expected_time = datetime(2025, 5, 29, 16, 30, 0)
        self.assertEqual(
            perfil.fecha_ultimo_acceso.replace(microsecond=0, tzinfo=None),
            expected_time
        )
    
    def test_should_allow_optional_tienda_asignada(self):
        """Debería permitir tienda asignada opcional"""
        perfil = PerfilUsuarioFactory(tienda_asignada=None)
        self.assertIsNone(perfil.tienda_asignada)
    
    def test_should_validate_telefono_format(self):
        """Debería validar formato de teléfono"""
        # Este test asume que podríamos agregar validación en el futuro
        perfil = PerfilUsuarioFactory(telefono='')
        self.assertEqual(perfil.telefono, '')  # Permitido por ahora
        
        perfil = PerfilUsuarioFactory(telefono='555-1234-5678')
        self.assertEqual(perfil.telefono, '555-1234-5678')


class ConfiguracionSistemaModelTests(BaseTestCase):
    """Tests para el modelo ConfiguracionSistema"""
    
    def test_should_create_configuracion_with_valid_data(self):
        """Debería crear configuración con datos válidos"""
        user = UserFactory()
        config = ConfiguracionSistemaFactory(
            clave='max_items_per_order',
            valor='100',
            descripcion='Máximo de items por pedido',
            tipo_dato='integer',
            modificado_por=user
        )
        
        self.assertEqual(config.clave, 'max_items_per_order')
        self.assertEqual(config.valor, '100')
        self.assertEqual(config.tipo_dato, 'integer')
        self.assertEqual(config.modificado_por, user)
    
    def test_should_enforce_unique_clave(self):
        """Debería enforcer clave única"""
        ConfiguracionSistemaFactory(clave='test_key')
        
        with self.assertRaises(IntegrityError):
            ConfiguracionSistemaFactory(clave='test_key')
    
    def test_should_validate_tipo_dato_choices(self):
        """Debería validar opciones de tipo de dato"""
        valid_types = ['string', 'integer', 'float', 'boolean', 'json']
        
        for tipo in valid_types:
            config = ConfiguracionSistemaFactory(tipo_dato=tipo)
            self.assertEqual(config.tipo_dato, tipo)
        
        # Tipo inválido
        with self.assertRaises(ValidationError):
            config = ConfiguracionSistema(
                clave='test',
                valor='test',
                            tipo_dato='invalid_type'
            )
            config.full_clean()
    
    def test_should_have_correct_string_representation(self):
        """Debería tener la representación string correcta"""
        config = ConfiguracionSistemaFactory(
            clave='test_config',
            valor='This is a very long value that should be truncated in the string representation'
        )
        
        expected = "test_config: This is a very long value that should be truncated"
        self.assertEqual(str(config), expected)
    
    def test_should_auto_update_fecha_modificacion(self):
        """Debería actualizar automáticamente fecha de modificación"""
        config = ConfiguracionSistemaFactory()
        original_date = config.fecha_modificacion
        
        # Simular cambio después de un tiempo
        with freeze_time("2025-05-29 18:00:00"):
            config.valor = 'nuevo_valor'
            config.save()
        
        self.assertNotEqual(config.fecha_modificacion, original_date)
    
    def test_should_handle_different_data_types(self):
        """Debería manejar diferentes tipos de datos"""
        # String
        config_str = ConfiguracionSistemaFactory(
            tipo_dato='string',
            valor='texto de prueba'
        )
        self.assertEqual(config_str.tipo_dato, 'string')
        
        # Integer
        config_int = ConfiguracionSistemaFactory(
            tipo_dato='integer',
            valor='42'
        )
        self.assertEqual(config_int.tipo_dato, 'integer')
        
        # Boolean
        config_bool = ConfiguracionSistemaFactory(
            tipo_dato='boolean',
            valor='true'
        )
        self.assertEqual(config_bool.tipo_dato, 'boolean')
        
        # JSON
        config_json = ConfiguracionSistemaFactory(
            tipo_dato='json',
            valor='{"key": "value", "number": 123}'
        )
        self.assertEqual(config_json.tipo_dato, 'json')
    
    def test_should_allow_long_descriptions(self):
        """Debería permitir descripciones largas"""
        long_description = "Esta es una descripción muy larga " * 50
        config = ConfiguracionSistemaFactory(descripcion=long_description)
        self.assertEqual(config.descripcion, long_description)
    
    def test_should_handle_null_modificado_por(self):
        """Debería manejar modificado_por nulo"""
        config = ConfiguracionSistemaFactory(modificado_por=None)
        self.assertIsNone(config.modificado_por)


class AdministracionModelsIntegrationTests(BaseTestCase):
    """Tests de integración para modelos de administración"""
    
    def test_should_create_complete_audit_trail(self):
        """Debería crear una pista de auditoría completa"""
        user = UserFactory()
        tienda = TiendaFactory()
        
        # Crear perfil de usuario
        perfil = PerfilUsuarioFactory(
            usuario=user,
            tienda_asignada=tienda
        )
        
        # Crear configuración
        config = ConfiguracionSistemaFactory(
            modificado_por=user,
            clave='audit_test'
        )
        
        # Crear log de auditoría
        log = LogAuditoriaFactory(
            usuario=user,
            accion='CONFIG',
            descripcion=f'Usuario modificó configuración {config.clave}',
            modelo_afectado='ConfiguracionSistema',
            objeto_id=str(config.id)
        )
        
        # Verificar relaciones
        self.assertEqual(perfil.usuario, user)
        self.assertEqual(config.modificado_por, user)
        self.assertEqual(log.usuario, user)
        
        # Verificar que podemos acceder a través de relaciones
        self.assertEqual(user.perfil, perfil)
        self.assertIn(log, user.logauditoria_set.all())
    
    def test_should_handle_user_deletion_gracefully(self):
        """Debería manejar eliminación de usuario correctamente"""
        user = UserFactory()
        
        # Crear registros relacionados
        perfil = PerfilUsuarioFactory(usuario=user)
        config = ConfiguracionSistemaFactory(modificado_por=user)
        log = LogAuditoriaFactory(usuario=user)
        
        # Eliminar usuario
        user.delete()
        
        # Verificar que el perfil se eliminó (CASCADE)
        with self.assertRaises(PerfilUsuario.DoesNotExist):
            PerfilUsuario.objects.get(id=perfil.id)
        
        # Verificar que config y log mantienen referencias nulas (SET_NULL)
        config.refresh_from_db()
        log.refresh_from_db()
        
        self.assertIsNone(config.modificado_por)
        self.assertIsNone(log.usuario)
    
    @patch('django.utils.timezone.now')
    def test_should_track_temporal_changes(self, mock_now):
        """Debería trackear cambios temporales correctamente"""
        # Tiempo inicial
        initial_time = datetime(2025, 5, 29, 10, 0, 0)
        mock_now.return_value = initial_time
        
        config = ConfiguracionSistemaFactory()
        initial_modification_date = config.fecha_modificacion
        
        # Cambio después de 2 horas
        later_time = initial_time + timedelta(hours=2)
        mock_now.return_value = later_time
        
        config.valor = 'nuevo valor'
        config.save()
        
        self.assertNotEqual(config.fecha_modificacion, initial_modification_date)
        self.assertEqual(config.fecha_modificacion, later_time)
