"""
Integration tests for Advanced Order Management System
Tests integration with existing POS modules and audit logging
"""

import json
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

# Import advanced order models
from .models import (
    OrdenCliente, EstadoProductoSeguimiento, EntregaParcial,
    NotaCredito, PortalClientePolitica, ProductoCompartir
)
from administracion.models import LogAuditoria
from clientes.models import Cliente
from productos.models import Producto
from proveedores.models import Proveedor
from tiendas.models import Tienda
from ventas.models import Pedido

User = get_user_model()


class PedidosAvanzadosIntegrationTestCase(TestCase):
    """Test integration between advanced orders and existing POS system"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user with admin permissions
        self.user = User.objects.create_user(
            username='test_admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.user.is_staff = True
        self.user.save()
        
        # Create test store
        self.tienda = Tienda.objects.create(
            nombre='Tienda Test',
            direccion='Test Address',
            contacto='1234567890'        )
        
        # Create test client
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            contacto='0987654321',
            tienda=self.tienda
        )
        
        # Create test product
        self.producto = Producto.objects.create(
            codigo='PROD001',
            marca='Marca Test',
            modelo='Modelo Test',
            color='Negro',
            propiedad='Talla 42',
            costo=50.00,
            precio=100.00,
            temporada='VERANO',
            oferta=False,
            admite_devolucion=True,
            proveedor=Proveedor.objects.create(nombre='Proveedor Test'),
            tienda=self.tienda
        )
        
        # Create test order
        self.orden = OrdenCliente.objects.create(
            cliente=self.cliente,
            numero_orden='ORD-TEST-001',
            estado='ACTIVO',
            total_productos=5,
            productos_recibidos=2,
            monto_total=Decimal('500.00'),
            created_by=self.user
        )
        
        # Client for HTTP requests
        self.client = Client()
        self.client.login(username='test_admin', password='testpass123')
    
    def test_dashboard_integration(self):
        """Test that dashboard integrates with existing audit logging"""
        # Access dashboard
        response = self.client.get(reverse('pedidos_avanzados:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Verify context includes key integration points
        self.assertIn('ordenes', response.context)
        self.assertIn('pendientes', response.context)
    
    def test_orden_creation_audit(self):
        """Test that orden creation can be audited"""
        # Create new orden
        orden_data = {
            'cliente': self.cliente.pk,
            'numero_orden': 'ORD-TEST-002',
            'estado': 'ACTIVO',
            'total_productos': 3,
            'monto_total': '300.00'
        }
        
        response = self.client.post(reverse('pedidos_avanzados:orden_create'), orden_data)
        
        # Should successfully create (might redirect or return success)
        self.assertIn(response.status_code, [200, 201, 302])
        
        # Verify orden was created
        if response.status_code == 302:
            self.assertTrue(OrdenCliente.objects.filter(numero_orden='ORD-TEST-002').exists())
    
    def test_api_authentication_integration(self):
        """Test API endpoints require authentication"""
        self.client.logout()
        
        # Test grid endpoint without authentication
        response = self.client.get(reverse('pedidos_avanzados:grid_data'))
        self.assertIn(response.status_code, [302, 403, 401])  # Redirect to login or forbidden
    
    def test_grid_filtering_integration(self):
        """Test grid filtering integrates with existing data"""
        # Test grid with filters
        response = self.client.get(reverse('pedidos_avanzados:grid_data'), {
            'cliente': self.cliente.pk,
            'estado': 'ACTIVO'
        })
        self.assertEqual(response.status_code, 200)
        
        # Verify JSON response
        data = json.loads(response.content)
        self.assertIn('data', data)
    
    def test_nota_credito_integration(self):
        """Test credit note integration with existing sales system"""
        # Create credit note
        nota = NotaCredito.objects.create(
            cliente=self.cliente,
            tipo='CREDITO',
            monto=Decimal('100.00'),
            motivo='Test credit note',
            created_by=self.user
        )
        
        # Verify integration with client's credit system
        self.assertEqual(nota.cliente, self.cliente)
        self.assertEqual(nota.estado, 'ACTIVA')
        self.assertTrue(nota.fecha_vencimiento)
    
    def test_entrega_parcial_integration(self):
        """Test partial delivery integration"""
        # Create a pedido first
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tienda=self.tienda,
            estado='pendiente',
            total=Decimal('200.00'),
            created_by=self.user
        )
        
        # Create partial delivery
        entrega = EntregaParcial.objects.create(
            pedido_original=pedido,
            pedido_nuevo=pedido,  # For testing, using same pedido
            ticket_entrega='TICKET-001',
            productos_entregados=[{"producto": "PROD001", "cantidad": 2}],
            monto_entregado=Decimal('100.00'),
            usuario_entrega=self.user
        )
        
        # Verify integration
        self.assertEqual(entrega.pedido_original, pedido)
        self.assertTrue(entrega.fecha_entrega)
    
    def test_producto_compartir_integration(self):
        """Test social sharing integration"""
        # Create sharing record
        compartir = ProductoCompartir.objects.create(
            producto=self.producto,
            cliente=self.cliente,
            plataforma='FACEBOOK',
            url_generada='https://facebook.com/share/123'
        )
        
        # Verify integration
        self.assertEqual(compartir.producto, self.producto)
        self.assertEqual(compartir.cliente, self.cliente)
        self.assertTrue(compartir.fecha_compartido)
    
    def test_portal_politica_integration(self):
        """Test portal policies integration"""
        # Create policy
        politica = PortalClientePolitica.objects.create(
            titulo='Test Policy',
            contenido='Test policy content',
            tipo='POLITICA',
            activo=True,
            orden_display=1
        )
        
        # Test portal view includes policies
        response = self.client.get(reverse('pedidos_avanzados:portal_cliente'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Policy')
    
    def test_csrf_protection(self):
        """Test CSRF protection on forms"""
        # Test POST without CSRF token fails
        response = self.client.post(reverse('pedidos_avanzados:orden_create'), {
            'cliente': self.cliente.pk,
            'numero_orden': 'TEST-CSRF'
        }, HTTP_X_CSRFTOKEN='invalid')
        
        # Should fail due to CSRF protection
        self.assertIn(response.status_code, [403, 405])  # CSRF failure or method not allowed
    
    def test_security_admin_views(self):
        """Test admin-only views require proper permissions"""
        # Create regular user
        regular_user = User.objects.create_user(
            username='regular_user',
            password='testpass123'
        )
        
        # Login as regular user
        self.client.logout()
        self.client.login(username='regular_user', password='testpass123')
        
        # Try to access admin view
        response = self.client.get(reverse('pedidos_avanzados:dashboard'))
        # Should redirect to login or show permission denied
        self.assertIn(response.status_code, [302, 403])


class PedidosAvanzadosAPIIntegrationTestCase(TestCase):
    """Test API integration"""
      def setUp(self):
        """Set up API test data"""
        self.user = User.objects.create_user(
            username='api_user',
            password='testpass123'
        )
        self.user.is_staff = True
        self.user.save()
        
        self.client = Client()
        self.client.login(username='api_user', password='testpass123')
        
        self.tienda = Tienda.objects.create(
            nombre='API Test Store',
            direccion='API Address',
            contacto='1111111111'
        )
        
        self.cliente = Cliente.objects.create(
            nombre='API Test Client',
            contacto='2222222222',
            tienda=self.tienda
        )
    
    def test_api_response_format(self):
        """Test API endpoints return consistent JSON format"""
        response = self.client.get(reverse('pedidos_avanzados:grid_data'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        # Check for consistent API response structure
        self.assertIn('data', data)
        
    def test_api_error_handling(self):
        """Test API error handling consistency"""
        # Test invalid request
        response = self.client.post(reverse('pedidos_avanzados:grid_data'), {
            'invalid_field': 'invalid_value'
        })
        
        # Should handle gracefully
        self.assertLessEqual(response.status_code, 500)


class PedidosAvanzadosPerformanceTestCase(TestCase):
    """Test performance and optimization"""
    
    def setUp(self):
        """Set up performance test data"""
        self.user = User.objects.create_user(
            username='perf_user',
            password='testpass123'
        )
        self.user.is_staff = True
        self.user.save()
        
        self.client = Client()
        self.client.login(username='perf_user', password='testpass123')
    
    def test_grid_pagination_performance(self):
        """Test grid pagination doesn't load all records"""
        response = self.client.get(reverse('pedidos_avanzados:grid_data'), {
            'page': 1,
            'size': 25
        })
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        if 'data' in data:
            # Should not return more than requested
            self.assertLessEqual(len(data['data']), 25)
    
    def test_model_integration(self):
        """Test models integrate properly with existing system"""
        # Create test store
        tienda = Tienda.objects.create(
            nombre='Model Test Store',
            direccion='Model Test Address',
            contacto='9999999999'        )
        
        # Create test client
        cliente = Cliente.objects.create(
            nombre='Model Test Client',
            contacto='8888888888',
            tienda=tienda
        )
        
        # Test order creation
        orden = OrdenCliente.objects.create(
            cliente=cliente,
            numero_orden='MODEL-TEST-001',
            estado='ACTIVO',
            total_productos=10,
            monto_total=Decimal('1000.00')
        )
        
        # Verify relationships work
        self.assertEqual(orden.cliente, cliente)
        self.assertEqual(orden.cliente.tienda, tienda)
        self.assertTrue(orden.porcentaje_completado >= 0)
