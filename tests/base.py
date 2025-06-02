"""
Clases base simplificadas para tests del sistema POS
"""
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.conf import settings
from unittest.mock import Mock, patch
import tempfile
import shutil
import os

from .factories import (
    UserFactory, AdminUserFactory, TiendaFactory, 
    ProductoFactory, ClienteFactory, CajaAbiertaFactory
)

User = get_user_model()


class BaseTestCase(TestCase):
    """
    Clase base para todos los tests unitarios del sistema
    """
    
    def setUp(self):
        super().setUp()
        
        # Crear usuarios básicos
        self.admin_user = AdminUserFactory(username='admin_test')
        self.regular_user = UserFactory(username='regular_test')
        
        # Crear tienda por defecto
        self.tienda = TiendaFactory(nombre='Tienda Test')
        
        # Crear caja abierta por defecto
        self.caja = CajaAbiertaFactory(tienda=self.tienda)
    
    def create_test_products(self, count=3):
        """Crea productos de prueba"""
        return [ProductoFactory(tienda=self.tienda) for _ in range(count)]
    
    def create_test_client(self):
        """Crea un cliente de prueba"""
        return ClienteFactory(tienda=self.tienda)
    
    def assertDecimalEqual(self, first, second, places=2, msg=None):
        """Assert para comparar decimales con precisión específica"""
        first_rounded = round(first, places)
        second_rounded = round(second, places)
        self.assertEqual(first_rounded, second_rounded, msg)


class BaseIntegrationTestCase(TransactionTestCase):
    """
    Clase base para tests de integración que requieren transacciones
    """
    
    def setUp(self):
        super().setUp()
        
        # Configurar base de datos
        call_command('migrate', verbosity=0, interactive=False)
        
        # Crear datos básicos
        self.admin_user = AdminUserFactory(username='admin_integration')
        self.tienda = TiendaFactory(nombre='Tienda Integración')
        self.caja = CajaAbiertaFactory(tienda=self.tienda)
    
    def tearDown(self):
        """Cleanup después de cada test"""
        self._clear_test_data()
        super().tearDown()
    
    def _clear_test_data(self):
        """Limpia datos de prueba"""
        # En lugar de usar flush, eliminar selectivamente
        from django.apps import apps
        
        # Obtener todos los modelos de las apps de negocio
        business_apps = ['productos', 'ventas', 'clientes', 'inventario', 'caja', 'proveedores']
        for app_label in business_apps:
            try:
                app = apps.get_app_config(app_label)
                for model in app.get_models():
                    model.objects.all().delete()
            except LookupError:
                pass  # App no encontrada, continuar


class MockedExternalServicesTestCase(BaseTestCase):
    """
    Clase base para tests que requieren mockear servicios externos
    """
    
    def setUp(self):
        super().setUp()
        self.patches = []
        
        # Mock común para servicios externos
        self.mock_email_service = self.add_patch('django.core.mail.send_mail')
        self.mock_payment_service = self.add_patch('sistema_pos.services.payment_service')
        
    def add_patch(self, target, **kwargs):
        """Helper para agregar patches de forma controlada"""
        patcher = patch(target, **kwargs)
        mock_obj = patcher.start()
        self.patches.append(patcher)
        return mock_obj
    
    def tearDown(self):
        """Cleanup de patches"""
        for patcher in self.patches:
            patcher.stop()
        super().tearDown()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
)
class PerformanceTestCase(BaseTestCase):
    """
    Clase base para tests de rendimiento
    """
    
    def setUp(self):
        super().setUp()
        import time
        self.start_time = time.time()
    
    def tearDown(self):
        super().tearDown()
        import time
        end_time = time.time()
        test_duration = end_time - self.start_time
        
        # Log tiempo de ejecución si es mayor a 1 segundo
        if test_duration > 1.0:
            print(f"\nTest {self._testMethodName} tardó {test_duration:.2f} segundos")
    
    def assertExecutionTime(self, callable_obj, max_seconds=1.0, *args, **kwargs):
        """Verifica que una operación no exceda el tiempo máximo"""
        import time
        start = time.time()
        result = callable_obj(*args, **kwargs)
        duration = time.time() - start
        
        self.assertLessEqual(
            duration, max_seconds,
            f"Operación tardó {duration:.2f}s, máximo permitido: {max_seconds}s"
        )
        return result


class ConcurrencyTestCase(BaseIntegrationTestCase):
    """
    Clase base para tests de concurrencia
    """
    
    def run_concurrent_operations(self, operations, num_threads=3):
        """Ejecuta operaciones de forma concurrente"""
        import threading
        import time
        
        results = []
        errors = []
        
        def run_operation(op):
            try:
                result = op()
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        threads = []
        for operation in operations:
            for _ in range(num_threads):
                thread = threading.Thread(target=run_operation, args=(operation,))
                threads.append(thread)
        
        # Iniciar todos los threads
        for thread in threads:
            thread.start()
        
        # Esperar a que terminen
        for thread in threads:
            thread.join(timeout=30)  # 30 segundos timeout
        
        return results, errors
