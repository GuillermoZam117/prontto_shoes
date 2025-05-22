"""
Tests for the cache manager component of the synchronization module.
"""
from django.test import TestCase, override_settings
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from tiendas.models import Tienda
from productos.models import Producto, Catalogo
from sincronizacion.cache_manager import CacheManager, cache_manager, detectar_estado_conexion
import os
import tempfile
import shutil
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Create a temporary directory for cache tests
TEMP_CACHE_DIR = tempfile.mkdtemp()

@override_settings(SINCRONIZACION_CACHE_DIR=TEMP_CACHE_DIR)
class CacheManagerTest(TestCase):
    """Test case for the cache manager functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='test_user',
            password='password123'
        )
          # Create test tienda
        self.tienda = Tienda.objects.create(
            nombre='Tienda Test',
            direccion='Calle Test 123',
            telefono='555-123-4567',
            email='tiendatest@example.com',
            responsable=self.user
        )
        
        # Create test categories and products
        self.catalogo = Catalogo.objects.create(
            nombre='Catalogo Test',
            temporada='Primavera 2025'
        )
        
        self.producto = Producto.objects.create(
            codigo='PT001',
            marca='Marca Test',
            modelo='Modelo Test',
            color='Negro',
            propiedad='Talla 42',
            costo=80.00,
            precio=100.00,
            temporada='Primavera 2025',
            tienda=self.tienda,
            catalogo=self.catalogo
        )
        
        # Initialize cache manager
        self.cache_manager = CacheManager()
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove temporary cache directory
        shutil.rmtree(TEMP_CACHE_DIR, ignore_errors=True)
    
    def test_cachear_modelo(self):
        """Test caching a model"""
        # Cache the product
        self.cache_manager.cachear_modelo(Producto, self.producto.id)
        
        # Check if product is in cache
        cache_key = f"{self.cache_manager.CACHE_PREFIX}Producto_{self.producto.id}"
        cached_data = self.cache_manager.obtener_de_cache(cache_key)
        
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data.get('id'), self.producto.id)
        self.assertEqual(cached_data.get('nombre'), 'Producto Test')
    
    def test_guardar_en_disco(self):
        """Test saving cache to disk"""
        # Cache the product
        self.cache_manager.cachear_modelo(Producto, self.producto.id)
        
        # Save to disk
        cache_key = f"{self.cache_manager.CACHE_PREFIX}Producto_{self.producto.id}"
        self.cache_manager.guardar_en_disco(cache_key)
        
        # Check if file exists
        file_path = os.path.join(TEMP_CACHE_DIR, f"Producto_{self.producto.id}.json")
        self.assertTrue(os.path.exists(file_path))
        
        # Check file content
        with open(file_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data.get('nombre'), 'Producto Test')
    
    def test_cargar_desde_disco(self):
        """Test loading cache from disk"""
        # Cache the product and save to disk
        self.cache_manager.cachear_modelo(Producto, self.producto.id)
        cache_key = f"{self.cache_manager.CACHE_PREFIX}Producto_{self.producto.id}"
        self.cache_manager.guardar_en_disco(cache_key)
        
        # Clear cache
        self.cache_manager.limpiar_cache()
        
        # Load from disk
        self.cache_manager.cargar_desde_disco(f"Producto_{self.producto.id}")
        
        # Check if product is in cache
        cached_data = self.cache_manager.obtener_de_cache(cache_key)
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data.get('nombre'), 'Producto Test')
    
    @patch('sincronizacion.cache_manager.requests.get')
    def test_detectar_estado_conexion_online(self, mock_get):
        """Test connection detection when online"""
        # Mock successful connection
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_get.return_value = mock_response
        
        is_online = detectar_estado_conexion()
        self.assertTrue(is_online)
    
    @patch('sincronizacion.cache_manager.requests.get')
    def test_detectar_estado_conexion_offline(self, mock_get):
        """Test connection detection when offline"""
        # Mock failed connection
        mock_get.side_effect = Exception("Connection error")
        
        is_online = detectar_estado_conexion()
        self.assertFalse(is_online)
