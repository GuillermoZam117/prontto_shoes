"""
Integration tests for the entire synchronization process.
"""
from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.cache import cache
from django.apps import apps
from tiendas.models import Tienda
from productos.models import Producto, Categoria
from sincronizacion.models import ColaSincronizacion, EstadoSincronizacion, TipoOperacion
from sincronizacion.cache_manager import CacheManager, cache_manager
from sincronizacion.conflict_resolution import ConflictResolver, ConflictResolutionStrategy
from sincronizacion.tasks import procesar_cola_sincronizacion
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import json
import os

# Create a temporary directory for cache tests
TEMP_CACHE_DIR = tempfile.mkdtemp()

@override_settings(SINCRONIZACION_CACHE_DIR=TEMP_CACHE_DIR)
class IntegrationSyncTest(TestCase):
    """Integration test for the complete synchronization process"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user_central = User.objects.create_user(
            username='central_admin',
            password='password123'
        )
        self.user_tienda = User.objects.create_user(
            username='tienda_admin',
            password='password456'
        )
        
        # Create test tiendas
        self.tienda_central = Tienda.objects.create(
            nombre='Tienda Central',
            direccion='Calle Principal 100',
            telefono='555-000-0000',
            email='central@example.com',
            responsable=self.user_central,
            es_central=True
        )
        
        self.tienda_sucursal = Tienda.objects.create(
            nombre='Tienda Sucursal',
            direccion='Calle Secundaria 200',
            telefono='555-111-1111',
            email='sucursal@example.com',
            responsable=self.user_tienda
        )
        
        # Create test category
        self.categoria = Categoria.objects.create(
            nombre='Calzado Deportivo',
            descripcion='Zapatos deportivos de alta calidad'
        )
        
        # Create a test product in the central store
        self.producto_central = Producto.objects.create(
            nombre='Zapatilla Runner Pro',
            codigo='ZRP100',
            descripcion='Zapatilla para corredores profesionales',
            precio=199.99,
            stock=50,
            categoria=self.categoria,
            tienda=self.tienda_central
        )
        
        # Initialize cache manager
        self.cache_manager = CacheManager()
        
        # Initialize conflict resolver
        self.conflict_resolver = ConflictResolver()
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove temporary cache directory
        shutil.rmtree(TEMP_CACHE_DIR, ignore_errors=True)
        # Clear Django cache
        cache.clear()
    
    @patch('sincronizacion.tasks.requests.post')
    def test_end_to_end_sync_process(self, mock_post):
        """Test the complete synchronization process from creation to conflict resolution"""
        # 1. ESCENARIO: La tienda central actualiza un producto
        
        # Simulate a product update in the central store
        self.producto_central.precio = 209.99
        self.producto_central.save()
        
        # 2. ESCENARIO: Se crea una operación de sincronización
        
        # Create a synchronization operation
        operacion = ColaSincronizacion.objects.create(
            tienda_origen=self.tienda_central,
            tienda_destino=self.tienda_sucursal,
            modelo_tipo='productos.Producto',
            modelo_id=self.producto_central.id,
            operacion=TipoOperacion.ACTUALIZAR,
            estado=EstadoSincronizacion.PENDIENTE,
            datos={
                'id': self.producto_central.id,
                'nombre': self.producto_central.nombre,
                'codigo': self.producto_central.codigo,
                'descripcion': self.producto_central.descripcion,
                'precio': float(self.producto_central.precio),
                'stock': self.producto_central.stock
            }
        )
        
        # 3. ESCENARIO: La tienda sucursal está offline
        
        # Simulate offline mode - cache the product for offline use
        self.cache_manager.cachear_modelo(Producto, self.producto_central.id)
        
        # Verify product is in cache
        cache_key = f"sync_cache_Producto_{self.producto_central.id}"
        cached_data = self.cache_manager.obtener_de_cache(cache_key)
        self.assertIsNotNone(cached_data)
        
        # 4. ESCENARIO: La sucursal también modifica el producto offline
        
        # Create a different version in the branch store (will create conflict)
        producto_sucursal = Producto.objects.create(
            nombre='Zapatilla Runner Pro',  # Same name
            codigo='ZRP100',                # Same code
            descripcion='Zapatilla para corredores profesionales',
            precio=189.99,                  # Different price
            stock=20,                       # Different stock
            categoria=self.categoria,
            tienda=self.tienda_sucursal
        )
        
        # Create sync operation from branch to central
        operacion_sucursal = ColaSincronizacion.objects.create(
            tienda_origen=self.tienda_sucursal,
            tienda_destino=self.tienda_central,
            modelo_tipo='productos.Producto',
            modelo_id=producto_sucursal.id,
            operacion=TipoOperacion.ACTUALIZAR,
            estado=EstadoSincronizacion.PENDIENTE,
            datos={
                'id': producto_sucursal.id,
                'nombre': producto_sucursal.nombre,
                'codigo': producto_sucursal.codigo,
                'descripcion': producto_sucursal.descripcion,
                'precio': float(producto_sucursal.precio),
                'stock': producto_sucursal.stock
            }
        )
        
        # 5. ESCENARIO: Se detectan conflictos
        
        # Detect conflicts
        conflicts = self.conflict_resolver.detectar_conflictos(
            modelo_tipo='productos.Producto',
            codigo='ZRP100'
        )
        
        # Should find 2 conflicts
        self.assertEqual(len(conflicts), 2)
        
        # Verify operations are marked as conflicts
        operacion.refresh_from_db()
        operacion_sucursal.refresh_from_db()
        self.assertEqual(operacion.estado, EstadoSincronizacion.CONFLICTO)
        self.assertEqual(operacion_sucursal.estado, EstadoSincronizacion.CONFLICTO)
        
        # 6. ESCENARIO: Se resuelven los conflictos
        
        # Resolve conflicts using field-specific strategy
        resolved = self.conflict_resolver.resolver_todos_conflictos(
            modelo_tipo='productos.Producto',
            codigo='ZRP100',
            strategy=ConflictResolutionStrategy.MEZCLAR_CAMPOS,
            field_priorities={
                'nombre': 'central',
                'descripcion': 'central',
                'precio': 'central',      # Use central price
                'stock': 'sumar'          # Sum both stocks
            }
        )
        
        # Should have 1 resolved operation
        self.assertEqual(len(resolved), 1)
        
        # Verify state of operations
        operacion.refresh_from_db()
        operacion_sucursal.refresh_from_db()
        
        # One should be pending, one completed
        self.assertTrue(
            (operacion.estado == EstadoSincronizacion.PENDIENTE and 
             operacion_sucursal.estado == EstadoSincronizacion.COMPLETADO) or
            (operacion.estado == EstadoSincronizacion.COMPLETADO and 
             operacion_sucursal.estado == EstadoSincronizacion.PENDIENTE)
        )
        
        # Get the winning operation
        winner = operacion if operacion.estado == EstadoSincronizacion.PENDIENTE else operacion_sucursal
        
        # Verify merged data
        merged_data = winner.datos
        self.assertEqual(merged_data['precio'], 209.99)  # Central price
        self.assertEqual(merged_data['stock'], 70)       # Sum of stocks (50+20)
        
        # 7. ESCENARIO: Se procesa la cola de sincronización
        
        # Mock API response for sync
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'success'}
        mock_post.return_value = mock_response
        
        # Process the queue
        procesar_cola_sincronizacion()
        
        # Verify the operation was processed
        winner.refresh_from_db()
        self.assertEqual(winner.estado, EstadoSincronizacion.COMPLETADO)
        
        # 8. ESCENARIO: Verificar sincronización completa
        
        # Check if the API was called with the correct data
        self.assertTrue(mock_post.called)
        call_args = mock_post.call_args[1]
        self.assertIn('json', call_args)
        
        # Verify the payload contains the merged data
        payload = call_args['json']
        self.assertEqual(payload['precio'], 209.99)
        self.assertEqual(payload['stock'], 70)
