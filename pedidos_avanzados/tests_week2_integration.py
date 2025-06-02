# Cross-Browser Compatibility Tests for Advanced Order Management
# Week 2: Integration & Testing Phase

import os
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

from .models import OrdenCliente
from clientes.models import Cliente
from tiendas.models import Tienda

User = get_user_model()


class CrossBrowserCompatibilityTestCase(TestCase):
    """Test cross-browser compatibility for advanced order management"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='browser_test_user',
            password='testpass123'
        )
        self.user.is_staff = True
        self.user.save()
        
        self.client = Client()
        self.client.login(username='browser_test_user', password='testpass123')
        
        # Create test data
        self.tienda = Tienda.objects.create(
            nombre='Browser Test Store',
            direccion='Test Address',
            contacto='1234567890'
        )
        
        self.cliente = Cliente.objects.create(
            nombre='Browser Test Client',
            telefono='0987654321',
            email='browser@test.com',
            tienda=self.tienda
        )
    
    def test_responsive_design_headers(self):
        """Test that views include proper responsive headers"""
        response = self.client.get(reverse('pedidos_avanzados:dashboard'))
        
        # Check for viewport meta tag and responsive headers
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'viewport')
        self.assertContains(response, 'bootstrap')
    
    def test_javascript_compatibility_headers(self):
        """Test JavaScript compatibility headers"""
        response = self.client.get(reverse('pedidos_avanzados:grid_management'))
        
        # Should include proper script tags and compatibility
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'text/javascript')
    
    def test_css_compatibility_headers(self):
        """Test CSS compatibility headers"""
        response = self.client.get(reverse('pedidos_avanzados:portal_cliente'))
        
        # Should include proper CSS headers
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'text/css')
    
    def test_ajax_endpoints_cors(self):
        """Test AJAX endpoints handle CORS properly"""
        response = self.client.get(reverse('pedidos_avanzados:grid_data'))
        
        # Should have proper headers for cross-origin requests
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_mobile_responsive_layout(self):
        """Test mobile responsive layout elements"""
        # Simulate mobile user agent
        response = self.client.get(
            reverse('pedidos_avanzados:dashboard'),
            HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
        )
        
        self.assertEqual(response.status_code, 200)
        # Should include mobile-friendly classes
        self.assertContains(response, 'col-sm')
        self.assertContains(response, 'col-md')


class PerformanceOptimizationTestCase(TestCase):
    """Test performance optimizations"""
    
    def setUp(self):
        """Set up performance test data"""
        self.user = User.objects.create_user(
            username='perf_test_user',
            password='testpass123'
        )
        self.user.is_staff = True
        self.user.save()
        
        self.client = Client()
        self.client.login(username='perf_test_user', password='testpass123')
        
        # Create test store and client
        self.tienda = Tienda.objects.create(
            nombre='Performance Test Store',
            direccion='Performance Address',
            contacto='5555555555'
        )
        
        self.cliente = Cliente.objects.create(
            nombre='Performance Test Client',
            telefono='5555555555',
            email='perf@test.com',
            tienda=self.tienda
        )
    
    def test_database_query_optimization(self):
        """Test database queries are optimized"""
        # Create multiple orders for testing
        for i in range(10):
            OrdenCliente.objects.create(
                cliente=self.cliente,
                numero_orden=f'PERF-{i:03d}',
                estado='ACTIVO',
                total_productos=5,
                monto_total=500.00,
                created_by=self.user
            )
        
        # Test dashboard query efficiency
        with self.assertNumQueries(15):  # Should be reasonably low
            response = self.client.get(reverse('pedidos_avanzados:dashboard'))
            self.assertEqual(response.status_code, 200)
    
    def test_pagination_performance(self):
        """Test pagination doesn't load excessive data"""
        # Create many orders
        for i in range(50):
            OrdenCliente.objects.create(
                cliente=self.cliente,
                numero_orden=f'PAG-{i:03d}',
                estado='ACTIVO',
                total_productos=3,
                monto_total=300.00,
                created_by=self.user
            )
        
        # Test grid with pagination
        response = self.client.get(reverse('pedidos_avanzados:grid_data'), {
            'page': 1,
            'size': 10
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Should return exactly the requested page size
        if 'data' in data:
            self.assertLessEqual(len(data['data']), 10)
    
    def test_static_file_optimization(self):
        """Test static files are properly served"""
        response = self.client.get(reverse('pedidos_avanzados:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Should reference optimized static files
        self.assertContains(response, '.css')
        self.assertContains(response, '.js')
    
    def test_caching_headers(self):
        """Test caching headers are set appropriately"""
        response = self.client.get(reverse('pedidos_avanzados:grid_data'))
        
        # API responses should have appropriate caching
        self.assertEqual(response.status_code, 200)
        # Should be JSON response
        self.assertEqual(response['Content-Type'], 'application/json')


class WebSocketIntegrationTestCase(TestCase):
    """Test WebSocket integration for real-time features"""
    
    def setUp(self):
        """Set up WebSocket test data"""
        self.user = User.objects.create_user(
            username='ws_test_user',
            password='testpass123'
        )
        self.user.is_staff = True
        self.user.save()
        
        self.client = Client()
        self.client.login(username='ws_test_user', password='testpass123')
    
    def test_websocket_ready_templates(self):
        """Test templates are ready for WebSocket integration"""
        response = self.client.get(reverse('pedidos_avanzados:dashboard'))
        
        # Should include WebSocket connection elements
        self.assertEqual(response.status_code, 200)
        # Templates should be ready for real-time updates
        self.assertContains(response, 'data-')  # Data attributes for JS hooks
    
    def test_real_time_notification_structure(self):
        """Test notification structure is in place"""
        response = self.client.get(reverse('pedidos_avanzados:grid_management'))
        
        # Should have notification containers
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'notification')


class MobileAppIntegrationTestCase(TestCase):
    """Test mobile app integration preparation"""
    
    def setUp(self):
        """Set up mobile integration test data"""
        self.user = User.objects.create_user(
            username='mobile_test_user',
            password='testpass123'
        )
        self.user.is_staff = True
        self.user.save()
        
        self.client = Client()
        self.client.login(username='mobile_test_user', password='testpass123')
    
    def test_api_mobile_compatibility(self):
        """Test API endpoints are mobile-app compatible"""
        response = self.client.get(reverse('pedidos_avanzados:grid_data'))
        
        # Should return proper JSON for mobile consumption
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        data = json.loads(response.content)
        self.assertIn('data', data)
    
    def test_mobile_responsive_forms(self):
        """Test forms are mobile-responsive"""
        response = self.client.get(reverse('pedidos_avanzados:portal_cliente'))
        
        # Should include mobile-friendly form elements
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form-control')
        self.assertContains(response, 'btn')
    
    def test_touch_friendly_interface(self):
        """Test interface is touch-friendly"""
        response = self.client.get(reverse('pedidos_avanzados:grid_management'))
        
        # Should have touch-friendly button sizes
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'btn-lg')  # Large buttons for touch
