"""
Tests for API viewsets in caja app to improve code coverage
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model
from caja.models import Caja, NotaCargo, Factura, TransaccionCaja
from tiendas.models import Tienda
from ventas.models import Pedido
from clientes.models import Cliente, Anticipo
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils.timezone import make_aware
from rest_framework import status
import json

User = get_user_model()

class CajaAPIViewsetsTest(APITestCase):
    """
    Tests for API viewsets in the caja module, focusing on:
    - CajaViewSet (with custom actions abrir_caja, cerrar_caja)
    - TransaccionCajaViewSet
    - MovimientosCajaReporteAPIView
    """
    
    def setUp(self):
        # Create user with tienda
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass',
            email='test@example.com'
        )
        
        # Create test stores
        self.tienda1 = Tienda.objects.create(
            nombre='Tienda Central', 
            direccion='Calle Principal 123'
        )
        self.tienda2 = Tienda.objects.create(
            nombre='Tienda Sucursal', 
            direccion='Av. Secundaria 456'
        )
        
        # Associate user with store
        self.user.tienda = self.tienda1
        self.user.save()
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Set dates
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
        
        # Create open cash register for today
        self.caja_abierta = Caja.objects.create(
            tienda=self.tienda1,
            fecha=self.today,
            fondo_inicial=Decimal('1000.00'),
            ingresos=Decimal('0.00'),
            egresos=Decimal('0.00'),
            saldo_final=Decimal('1000.00'),
            cerrada=False,
            created_by=self.user
        )
        
        # Create closed cash register for yesterday
        self.caja_cerrada = Caja.objects.create(
            tienda=self.tienda1,
            fecha=self.yesterday,
            fondo_inicial=Decimal('500.00'),
            ingresos=Decimal('1500.00'),
            egresos=Decimal('200.00'),
            saldo_final=Decimal('1800.00'),
            cerrada=True,
            created_by=self.user
        )
        
        # Create test customer
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test', 
            tienda=self.tienda1
        )
        
        # Create test order
        self.pedido = Pedido.objects.create(
            cliente=self.cliente,
            fecha=make_aware(datetime.now()),
            estado='completado',
            total=Decimal('300.00'),
            tienda=self.tienda1,
            tipo='venta',
            descuento_aplicado=Decimal('0.00')
        )
        
        # Create test transactions
        self.transaccion_venta = TransaccionCaja.objects.create(
            caja=self.caja_abierta,
            tipo_movimiento='ingreso',
            monto=Decimal('300.00'),
            descripcion='Venta',
            pedido=self.pedido,
            created_by=self.user
        )
        
        # Create advance payment
        self.anticipo = Anticipo.objects.create(
            cliente=self.cliente,
            monto=Decimal('100.00'),
            fecha=self.today,
            created_by=self.user
        )
        
        self.transaccion_anticipo = TransaccionCaja.objects.create(
            caja=self.caja_abierta,
            tipo_movimiento='ingreso',
            monto=Decimal('100.00'),
            descripcion='Anticipo',
            anticipo=self.anticipo,
            created_by=self.user
        )
        
        # Create charge note
        self.nota_cargo = NotaCargo.objects.create(
            caja=self.caja_abierta,
            monto=Decimal('50.00'),
            motivo='Gastos de limpieza',
            fecha=self.today,
            created_by=self.user
        )
        
        self.transaccion_egreso = TransaccionCaja.objects.create(
            caja=self.caja_abierta,
            tipo_movimiento='egreso',
            monto=Decimal('50.00'),
            descripcion='Nota de Cargo',
            nota_cargo=self.nota_cargo,
            created_by=self.user
        )
    
    def test_caja_viewset_list(self):
        """Test list endpoint of CajaViewSet"""
        url = reverse('caja-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # should list both cajas
        
        # Test filtering by fecha
        response = self.client.get(f"{url}?fecha={self.today.isoformat()}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test filtering by tienda
        response = self.client.get(f"{url}?tienda={self.tienda1.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Test filtering by cerrada
        response = self.client.get(f"{url}?cerrada=false")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.caja_abierta.pk)
    
    def test_caja_viewset_retrieve(self):
        """Test retrieve endpoint of CajaViewSet"""
        url = reverse('caja-detail', kwargs={'pk': self.caja_abierta.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.caja_abierta.pk)
        self.assertEqual(response.data['fecha'], self.today.isoformat())
        self.assertEqual(response.data['fondo_inicial'], '1000.00')
        self.assertEqual(response.data['cerrada'], False)
    
    def test_caja_viewset_create(self):
        """Test create endpoint of CajaViewSet"""
        url = reverse('caja-list')
        data = {
            'tienda': self.tienda2.pk,
            'fecha': self.today.isoformat(),
            'fondo_inicial': '2000.00',
            'saldo_final': '2000.00',
            'cerrada': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['tienda'], self.tienda2.pk)
        self.assertEqual(response.data['fondo_inicial'], '2000.00')
        
        # Verify cash register was created in the database
        new_caja = Caja.objects.get(pk=response.data['id'])
        self.assertEqual(new_caja.tienda.pk, self.tienda2.pk)
        self.assertEqual(new_caja.fondo_inicial, Decimal('2000.00'))
    
    def test_caja_viewset_update(self):
        """Test update endpoint of CajaViewSet"""
        url = reverse('caja-detail', kwargs={'pk': self.caja_abierta.pk})
        data = {
            'tienda': self.tienda1.pk,
            'fecha': self.today.isoformat(),
            'fondo_inicial': '1200.00',  # Changed
            'saldo_final': '1200.00',    # Changed
            'cerrada': False
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['fondo_inicial'], '1200.00')
        
        # Verify cash register was updated in the database
        self.caja_abierta.refresh_from_db()
        self.assertEqual(self.caja_abierta.fondo_inicial, Decimal('1200.00'))
    
    def test_caja_viewset_partial_update(self):
        """Test partial update endpoint of CajaViewSet"""
        url = reverse('caja-detail', kwargs={'pk': self.caja_abierta.pk})
        data = {
            'fondo_inicial': '1500.00'  # Only update fondo_inicial
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['fondo_inicial'], '1500.00')
        
        # Verify cash register was updated in the database
        self.caja_abierta.refresh_from_db()
        self.assertEqual(self.caja_abierta.fondo_inicial, Decimal('1500.00'))
    
    def test_caja_viewset_delete(self):
        """Test delete endpoint of CajaViewSet"""
        # Create a cash register specifically for deleting
        temp_caja = Caja.objects.create(
            tienda=self.tienda2,
            fecha=self.today,
            fondo_inicial=Decimal('800.00'),
            cerrada=False,
            created_by=self.user
        )
        
        url = reverse('caja-detail', kwargs={'pk': temp_caja.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify cash register was deleted from the database
        with self.assertRaises(Caja.DoesNotExist):
            Caja.objects.get(pk=temp_caja.pk)
    
    def test_caja_viewset_abrir_caja_action(self):
        """Test abrir_caja custom action of CajaViewSet"""
        url = reverse('caja-abrir-caja')
        
        # Delete the existing open cash register to avoid conflict
        self.caja_abierta.delete()
        
        data = {
            'tienda_id': self.tienda1.pk,
            'fondo_inicial': '1500.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        # The API should create a new cash register
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['tienda'], self.tienda1.pk)
        self.assertEqual(response.data['fondo_inicial'], '1500.00')
        self.assertEqual(response.data['cerrada'], False)
        
        # Test with missing tienda_id
        data = {
            'fondo_inicial': '1500.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Test with non-existent tienda
        data = {
            'tienda_id': 9999,  # Non-existent ID
            'fondo_inicial': '1500.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        
        # Test opening a cash register when one is already open
        data = {
            'tienda_id': self.tienda1.pk,
            'fondo_inicial': '2000.00'
        }
        
        # Try to open another for the same store and date
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response.data)
    
    def test_caja_viewset_cerrar_caja_action(self):
        """Test cerrar_caja custom action of CajaViewSet"""
        url = reverse('caja-cerrar-caja')
        
        data = {
            'tienda_id': self.tienda1.pk,
            'fecha': self.today.isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the cash register is closed
        self.caja_abierta.refresh_from_db()
        self.assertTrue(self.caja_abierta.cerrada)
        
        # Verify the cash register has correct totals
        self.assertEqual(self.caja_abierta.ingresos, Decimal('400.00'))  # 300 + 100
        self.assertEqual(self.caja_abierta.egresos, Decimal('50.00'))
        self.assertEqual(self.caja_abierta.saldo_final, Decimal('1350.00'))  # 1000 + 400 - 50
        
        # Test with missing tienda_id
        data = {
            'fecha': self.today.isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Test with invalid date format
        data = {
            'tienda_id': self.tienda1.pk,
            'fecha': 'invalid-date'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Test trying to close a non-existent or already closed cash register
        data = {
            'tienda_id': self.tienda1.pk,
            'fecha': self.yesterday.isoformat()  # This cash register is already closed
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
      def test_transaccion_caja_viewset_list(self):
        """Test list endpoint of TransaccionCajaViewSet"""
        url = reverse('transaccioncaja-list')  # Correct URL name
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # should list all 3 transactions
        
        # Test filtering by caja
        response = self.client.get(f"{url}?caja={self.caja_abierta.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Test filtering by tipo_movimiento
        response = self.client.get(f"{url}?tipo_movimiento=ingreso")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        response = self.client.get(f"{url}?tipo_movimiento=egreso")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test filtering by pedido
        response = self.client.get(f"{url}?pedido={self.pedido.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test filtering by anticipo
        response = self.client.get(f"{url}?anticipo={self.anticipo.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test filtering by nota_cargo
        response = self.client.get(f"{url}?nota_cargo={self.nota_cargo.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
      def test_transaccion_caja_viewset_retrieve(self):
        """Test retrieve endpoint of TransaccionCajaViewSet"""
        url = reverse('transaccioncaja-detail', kwargs={'pk': self.transaccion_venta.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.transaccion_venta.pk)
        self.assertEqual(response.data['tipo_movimiento'], 'ingreso')
        self.assertEqual(response.data['monto'], '300.00')
        self.assertEqual(response.data['pedido'], self.pedido.pk)
      def test_transaccion_caja_viewset_create(self):
        """Test create endpoint of TransaccionCajaViewSet"""
        url = reverse('transaccioncaja-list')
        data = {
            'tipo_movimiento': 'ingreso',
            'monto': '150.00',
            'descripcion': 'Nueva venta'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['tipo_movimiento'], 'ingreso')
        self.assertEqual(response.data['monto'], '150.00')
        
        # Verify the caja is automatically set to the user's store open cash register
        self.assertEqual(response.data['caja'], self.caja_abierta.pk)
      def test_transaccion_caja_viewset_update(self):
        """Test update endpoint of TransaccionCajaViewSet"""
        url = reverse('transaccioncaja-detail', kwargs={'pk': self.transaccion_venta.pk})
        data = {
            'caja': self.caja_abierta.pk,
            'tipo_movimiento': 'ingreso',
            'monto': '350.00',  # Changed
            'descripcion': 'Venta actualizada',  # Changed
            'pedido': self.pedido.pk
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['monto'], '350.00')
        self.assertEqual(response.data['descripcion'], 'Venta actualizada')
        
        # Verify transaction was updated in the database
        self.transaccion_venta.refresh_from_db()
        self.assertEqual(self.transaccion_venta.monto, Decimal('350.00'))
        self.assertEqual(self.transaccion_venta.descripcion, 'Venta actualizada')
      def test_transaccion_caja_viewset_delete(self):
        """Test delete endpoint of TransaccionCajaViewSet"""
        # Create a transaction specifically for deleting
        temp_transaccion = TransaccionCaja.objects.create(
            caja=self.caja_abierta,
            tipo_movimiento='ingreso',
            monto=Decimal('75.00'),
            descripcion='Transacción temporal',
            created_by=self.user
        )
        
        url = reverse('transaccioncaja-detail', kwargs={'pk': temp_transaccion.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify transaction was deleted from the database
        with self.assertRaises(TransaccionCaja.DoesNotExist):
            TransaccionCaja.objects.get(pk=temp_transaccion.pk)
      def test_movimientos_caja_reporte_api(self):
        """Test MovimientosCajaReporteAPIView"""
        url = reverse('movimientos-caja-reporte')
        
        # Test without filters
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should return both cajas
        
        # Test with store filter
        response = self.client.get(f"{url}?tienda_id={self.tienda1.pk}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Both cajas are for tienda1
        
        # Test with date filter
        response = self.client.get(f"{url}?fecha={self.today.isoformat()}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only caja_abierta is for today
        
        # Check the structure of the response
        caja_data = response.data[0]
        self.assertEqual(caja_data['tienda_id'], self.tienda1.pk)
        
        # Since the response date might be in a different format, 
        # we'll check that it contains the correct year, month, and day
        fecha_str = caja_data['fecha']
        self.assertTrue(str(self.today.year) in fecha_str)
        self.assertTrue(str(self.today.month).zfill(2) in fecha_str.replace('-', ''))
        self.assertTrue(str(self.today.day).zfill(2) in fecha_str.replace('-', ''))
        
        self.assertEqual(len(caja_data['movimientos']), 3)  # 3 transactions for today's caja
        
        # Check transaction details in the response
        movimientos = caja_data['movimientos']
        self.assertTrue(any(m['tipo'] == 'ingreso' and float(m['monto']) == 300.00 for m in movimientos))
        self.assertTrue(any(m['tipo'] == 'ingreso' and float(m['monto']) == 100.00 for m in movimientos))
        self.assertTrue(any(m['tipo'] == 'egreso' and float(m['monto']) == 50.00 for m in movimientos))
        
        # Test with invalid date format
        response = self.client.get(f"{url}?fecha=invalid-date")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
