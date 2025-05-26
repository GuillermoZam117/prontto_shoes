from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import json

from caja.models import Caja, TransaccionCaja, Factura, NotaCargo
from caja.views import CajaViewSet, TransaccionCajaViewSet, FacturaViewSet
from caja.serializers import CajaSerializer, TransaccionCajaSerializer, FacturaSerializer
from ventas.models import Pedido
from tiendas.models import Tienda
from clientes.models import Cliente


class CajaViewSetTestCase(APITestCase):
    """Test suite for CajaViewSet"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and authenticate
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            password='testpass',
            is_staff=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create related objects
        self.tienda = Tienda.objects.create(
            nombre='Tienda Test', 
            direccion='Calle 1'
        )
        
        # Create a caja
        self.caja = Caja.objects.create(
            tienda=self.tienda,
            fecha=timezone.now().date(),
            fondo_inicial=Decimal('1000.00'),
            ingresos=Decimal('0.00'),
            egresos=Decimal('0.00'),
            saldo_final=Decimal('1000.00'),
            cerrada=False,
            created_by=self.user
        )
        
        # URLs for API calls
        self.list_url = reverse('api:caja-list')
        self.detail_url = reverse('api:caja-detail', kwargs={'pk': self.caja.pk})
    
    def test_list_cajas(self):
        """Test listing all cajas"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
    
    def test_retrieve_caja(self):
        """Test retrieving a specific caja"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.caja.pk)
        self.assertEqual(Decimal(response.data['fondo_inicial']), self.caja.fondo_inicial)
    
    def test_create_caja(self):
        """Test creating a new caja"""
        data = {
            'tienda': self.tienda.id,
            'fecha': (timezone.now().date() + timezone.timedelta(days=1)).isoformat(),
            'fondo_inicial': '1500.00',
            'ingresos': '0.00',
            'egresos': '0.00',
            'saldo_final': '1500.00',
            'cerrada': False
        }
        
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify caja was created
        nueva_caja = Caja.objects.get(fondo_inicial=Decimal('1500.00'))
        self.assertEqual(nueva_caja.tienda.id, self.tienda.id)
    
    def test_update_caja(self):
        """Test updating a caja"""
        data = {
            'tienda': self.tienda.id,
            'fecha': self.caja.fecha.isoformat(),
            'fondo_inicial': '1000.00',
            'ingresos': '500.00',  # Updated
            'egresos': '200.00',   # Updated
            'saldo_final': '1300.00',  # Updated
            'cerrada': False
        }
        
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify caja was updated
        self.caja.refresh_from_db()
        self.assertEqual(self.caja.ingresos, Decimal('500.00'))
        self.assertEqual(self.caja.egresos, Decimal('200.00'))
        self.assertEqual(self.caja.saldo_final, Decimal('1300.00'))
    
    def test_partial_update_caja(self):
        """Test partially updating a caja"""
        data = {
            'ingresos': '600.00',
            'saldo_final': '1600.00'
        }
        
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify caja was partially updated
        self.caja.refresh_from_db()
        self.assertEqual(self.caja.ingresos, Decimal('600.00'))
        self.assertEqual(self.caja.saldo_final, Decimal('1600.00'))
        # Original values should be preserved
        self.assertEqual(self.caja.fondo_inicial, Decimal('1000.00'))
    
    def test_cerrar_caja(self):
        """Test closing a caja"""
        url = reverse('api:caja-cerrar', kwargs={'pk': self.caja.pk})
        
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify caja was closed
        self.caja.refresh_from_db()
        self.assertTrue(self.caja.cerrada)
    
    def test_filter_cajas_by_tienda(self):
        """Test filtering cajas by tienda"""
        # Create another tienda
        otra_tienda = Tienda.objects.create(
            nombre='Otra Tienda', 
            direccion='Otra Calle'
        )
        
        # Create caja for another tienda
        Caja.objects.create(
            tienda=otra_tienda,
            fecha=timezone.now().date(),
            fondo_inicial=Decimal('2000.00'),
            saldo_final=Decimal('2000.00'),
            cerrada=False,
            created_by=self.user
        )
        
        # Filter by tienda
        url = f"{self.list_url}?tienda={self.tienda.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include cajas for this tienda
        for caja in response.data:
            self.assertEqual(caja['tienda'], self.tienda.id)
    
    def test_filter_cajas_by_fecha(self):
        """Test filtering cajas by date"""
        # Create caja for another date
        otra_fecha = timezone.now().date() - timezone.timedelta(days=1)
        Caja.objects.create(
            tienda=self.tienda,
            fecha=otra_fecha,
            fondo_inicial=Decimal('500.00'),
            saldo_final=Decimal('500.00'),
            cerrada=False,
            created_by=self.user
        )
        
        # Filter by fecha
        url = f"{self.list_url}?fecha={self.caja.fecha.isoformat()}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include cajas for this date
        for caja in response.data:
            self.assertEqual(caja['fecha'], self.caja.fecha.isoformat())
    
    def test_filter_cajas_by_cerrada(self):
        """Test filtering cajas by closed status"""
        # Create closed caja
        Caja.objects.create(
            tienda=self.tienda,
            fecha=timezone.now().date() + timezone.timedelta(days=1),
            fondo_inicial=Decimal('800.00'),
            saldo_final=Decimal('800.00'),
            cerrada=True,
            created_by=self.user
        )
        
        # Filter by cerrada=true
        url = f"{self.list_url}?cerrada=true"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include closed cajas
        for caja in response.data:
            self.assertTrue(caja['cerrada'])
        
        # Filter by cerrada=false
        url = f"{self.list_url}?cerrada=false"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include open cajas
        for caja in response.data:
            self.assertFalse(caja['cerrada'])


class TransaccionCajaViewSetTestCase(APITestCase):
    """Test suite for TransaccionCajaViewSet"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and authenticate
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            password='testpass',
            is_staff=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create related objects
        self.tienda = Tienda.objects.create(
            nombre='Tienda Test', 
            direccion='Calle 1'
        )
        
        # Create a caja
        self.caja = Caja.objects.create(
            tienda=self.tienda,
            fecha=timezone.now().date(),
            fondo_inicial=Decimal('1000.00'),
            ingresos=Decimal('200.00'),
            egresos=Decimal('100.00'),
            saldo_final=Decimal('1100.00'),
            cerrada=False,
            created_by=self.user
        )
        
        # Create a transaccion
        self.transaccion = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='ingreso',
            monto=Decimal('200.00'),
            descripcion='Venta',
            created_by=self.user
        )
        
        # URLs for API calls
        self.list_url = reverse('api:transaccioncaja-list')
        self.detail_url = reverse('api:transaccioncaja-detail', kwargs={'pk': self.transaccion.pk})
    
    def test_list_transacciones(self):
        """Test listing all transacciones"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
    
    def test_retrieve_transaccion(self):
        """Test retrieving a specific transaccion"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.transaccion.pk)
        self.assertEqual(Decimal(response.data['monto']), self.transaccion.monto)
    
    def test_create_transaccion(self):
        """Test creating a new transaccion"""
        data = {
            'caja': self.caja.id,
            'tipo_movimiento': 'egreso',
            'monto': '50.00',
            'descripcion': 'Pago proveedores'
        }
        
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify transaccion was created
        nueva_transaccion = TransaccionCaja.objects.get(descripcion='Pago proveedores')
        self.assertEqual(nueva_transaccion.monto, Decimal('50.00'))
        self.assertEqual(nueva_transaccion.tipo_movimiento, 'egreso')
        
        # Verify caja amounts were updated
        self.caja.refresh_from_db()
        self.assertEqual(self.caja.egresos, Decimal('150.00'))  # Original 100 + new 50
        self.assertEqual(self.caja.saldo_final, Decimal('1050.00'))  # Original 1100 - new 50
    
    def test_update_transaccion(self):
        """Test updating a transaccion"""
        data = {
            'caja': self.caja.id,
            'tipo_movimiento': 'ingreso',
            'monto': '300.00',  # Changed from 200 to 300
            'descripcion': 'Venta actualizada'
        }
        
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify transaccion was updated
        self.transaccion.refresh_from_db()
        self.assertEqual(self.transaccion.monto, Decimal('300.00'))
        self.assertEqual(self.transaccion.descripcion, 'Venta actualizada')
        
        # Verify caja amounts were updated
        self.caja.refresh_from_db()
        self.assertEqual(self.caja.ingresos, Decimal('300.00'))  # Changed from 200 to 300
        self.assertEqual(self.caja.saldo_final, Decimal('1200.00'))  # Original 1100 + 100 more
    
    def test_delete_transaccion(self):
        """Test deleting a transaccion"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify transaccion was deleted
        with self.assertRaises(TransaccionCaja.DoesNotExist):
            TransaccionCaja.objects.get(pk=self.transaccion.pk)
        
        # Verify caja amounts were updated
        self.caja.refresh_from_db()
        self.assertEqual(self.caja.ingresos, Decimal('0.00'))  # The 200 from transaction removed
        self.assertEqual(self.caja.saldo_final, Decimal('900.00'))  # Original 1100 - 200 from transaction
    
    def test_filter_transacciones_by_caja(self):
        """Test filtering transacciones by caja"""
        # Create another caja
        otra_caja = Caja.objects.create(
            tienda=self.tienda,
            fecha=timezone.now().date() + timezone.timedelta(days=1),
            fondo_inicial=Decimal('500.00'),
            saldo_final=Decimal('500.00'),
            cerrada=False,
            created_by=self.user
        )
        
        # Create transaccion for another caja
        TransaccionCaja.objects.create(
            caja=otra_caja,
            tipo_movimiento='ingreso',
            monto=Decimal('100.00'),
            descripcion='Otra venta',
            created_by=self.user
        )
        
        # Filter by caja
        url = f"{self.list_url}?caja={self.caja.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include transacciones for this caja
        for transaccion in response.data:
            self.assertEqual(transaccion['caja'], self.caja.id)
    
    def test_filter_transacciones_by_tipo(self):
        """Test filtering transacciones by type"""
        # Create an egreso transaccion
        TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='egreso',
            monto=Decimal('100.00'),
            descripcion='Gasto',
            created_by=self.user
        )
        
        # Filter by tipo_movimiento=ingreso
        url = f"{self.list_url}?tipo_movimiento=ingreso"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include ingreso transacciones
        for transaccion in response.data:
            self.assertEqual(transaccion['tipo_movimiento'], 'ingreso')
        
        # Filter by tipo_movimiento=egreso
        url = f"{self.list_url}?tipo_movimiento=egreso"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include egreso transacciones
        for transaccion in response.data:
            self.assertEqual(transaccion['tipo_movimiento'], 'egreso')


class FacturaViewSetTestCase(APITestCase):
    """Test suite for FacturaViewSet"""
    
    def setUp(self):
        """Set up test data"""
        # Create user and authenticate
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            password='testpass',
            is_staff=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create related objects
        self.tienda = Tienda.objects.create(
            nombre='Tienda Test', 
            direccion='Calle 1'
        )
        
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            correo='cliente@test.com'
        )
        
        # Create a pedido
        self.pedido = Pedido.objects.create(
            cliente=self.cliente,
            tienda=self.tienda,
            fecha=timezone.now().date(),
            estado='completado',
            total=Decimal('500.00'),
            pagado=True,
            created_by=self.user
        )
        
        # Create a factura
        self.factura = Factura.objects.create(
            pedido=self.pedido,
            folio='FACT-001',
            fecha=timezone.now().date(),
            total=Decimal('500.00'),
            created_by=self.user
        )
        
        # URLs for API calls
        self.list_url = reverse('api:factura-list')
        self.detail_url = reverse('api:factura-detail', kwargs={'pk': self.factura.pk})
    
    def test_list_facturas(self):
        """Test listing all facturas"""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
    
    def test_retrieve_factura(self):
        """Test retrieving a specific factura"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.factura.pk)
        self.assertEqual(response.data['folio'], 'FACT-001')
    
    def test_create_factura(self):
        """Test creating a new factura"""
        # Create another pedido for a new factura
        otro_pedido = Pedido.objects.create(
            cliente=self.cliente,
            tienda=self.tienda,
            fecha=timezone.now().date(),
            estado='completado',
            total=Decimal('600.00'),
            pagado=True,
            created_by=self.user
        )
        
        data = {
            'pedido': otro_pedido.id,
            'folio': 'FACT-002',
            'fecha': timezone.now().date().isoformat(),
            'total': '600.00'
        }
        
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify factura was created
        nueva_factura = Factura.objects.get(folio='FACT-002')
        self.assertEqual(nueva_factura.pedido.id, otro_pedido.id)
        self.assertEqual(nueva_factura.total, Decimal('600.00'))
    
    def test_update_factura(self):
        """Test updating a factura"""
        data = {
            'pedido': self.pedido.id,
            'folio': 'FACT-001-UPD',
            'fecha': self.factura.fecha.isoformat(),
            'total': '500.00'
        }
        
        response = self.client.put(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify factura was updated
        self.factura.refresh_from_db()
        self.assertEqual(self.factura.folio, 'FACT-001-UPD')
    
    def test_partial_update_factura(self):
        """Test partially updating a factura"""
        data = {
            'folio': 'FACT-001-PARTIAL'
        }
        
        response = self.client.patch(self.detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify factura was partially updated
        self.factura.refresh_from_db()
        self.assertEqual(self.factura.folio, 'FACT-001-PARTIAL')
        # Original values should be preserved
        self.assertEqual(self.factura.total, Decimal('500.00'))
    
    def test_delete_factura(self):
        """Test deleting a factura"""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify factura was deleted
        with self.assertRaises(Factura.DoesNotExist):
            Factura.objects.get(pk=self.factura.pk)
    
    def test_filter_facturas_by_folio(self):
        """Test filtering facturas by folio"""
        # Create another factura with different folio
        otro_pedido = Pedido.objects.create(
            cliente=self.cliente,
            tienda=self.tienda,
            fecha=timezone.now().date(),
            estado='completado',
            total=Decimal('700.00'),
            pagado=True,
            created_by=self.user
        )
        
        Factura.objects.create(
            pedido=otro_pedido,
            folio='FACT-003',
            fecha=timezone.now().date(),
            total=Decimal('700.00'),
            created_by=self.user
        )
        
        # Filter by folio
        url = f"{self.list_url}?folio=FACT-001"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include facturas with matching folio
        for factura in response.data:
            self.assertTrue('FACT-001' in factura['folio'])
    
    def test_filter_facturas_by_fecha(self):
        """Test filtering facturas by fecha"""
        # Create another factura with different date
        otro_pedido = Pedido.objects.create(
            cliente=self.cliente,
            tienda=self.tienda,
            fecha=timezone.now().date() - timezone.timedelta(days=1),
            estado='completado',
            total=Decimal('800.00'),
            pagado=True,
            created_by=self.user
        )
        
        otra_fecha = timezone.now().date() - timezone.timedelta(days=1)
        Factura.objects.create(
            pedido=otro_pedido,
            folio='FACT-004',
            fecha=otra_fecha,
            total=Decimal('800.00'),
            created_by=self.user
        )
        
        # Filter by fecha
        url = f"{self.list_url}?fecha={self.factura.fecha.isoformat()}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only include facturas with matching fecha
        for factura in response.data:
            self.assertEqual(factura['fecha'], self.factura.fecha.isoformat())
    
    def test_get_pdf(self):
        """Test getting factura PDF"""
        url = reverse('api:factura-pdf', kwargs={'pk': self.factura.pk})
        response = self.client.get(url)
        
        # The response should be a PDF file
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(f'attachment; filename="factura_{self.factura.folio}', response['Content-Disposition'])
