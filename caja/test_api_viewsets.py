"""
Tests for API viewsets in caja app to improve code coverage
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth import get_user_model
from caja.models import Caja, NotaCargo, Factura, TransaccionCaja
from caja.serializers import CajaSerializer, TransaccionCajaSerializer
from tiendas.models import Tienda
from ventas.models import Pedido
from clientes.models import Cliente, Anticipo
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils.timezone import make_aware
from rest_framework import status

User = get_user_model()

class CajaAPITest(APITestCase):
    """
    Tests for CajaViewSet API with custom actions (abrir_caja, cerrar_caja)
    """
    
    def setUp(self):
        # Create user
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
    
    def test_caja_viewset_abrir_caja_action(self):
        """Test abrir_caja custom action of CajaViewSet"""
        # Delete the existing open cash register for this store and date
        self.caja_abierta.delete()
        
        url = reverse('caja-abrir-caja')
        data = {
            'tienda_id': self.tienda1.pk,
            'fondo_inicial': '1500.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['tienda'], self.tienda1.pk)
        self.assertEqual(response.data['fondo_inicial'], '1500.00')
        self.assertEqual(response.data['cerrada'], False)
        
        # Test already open cash register
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response.data)
    
    def test_caja_viewset_cerrar_caja_action(self):
        """Test cerrar_caja custom action of CajaViewSet"""
        # Create a test customer
        cliente = Cliente.objects.create(
            nombre='Cliente Test', 
            tienda=self.tienda1
        )
        
        # Create test order
        pedido = Pedido.objects.create(
            cliente=cliente,
            fecha=make_aware(datetime.now()),
            estado='completado',
            total=Decimal('300.00'),
            tienda=self.tienda1,
            tipo='venta',
            descuento_aplicado=Decimal('0.00')
        )
        
        # Create transactions for the cash register
        TransaccionCaja.objects.create(
            caja=self.caja_abierta,
            tipo_movimiento='ingreso',
            monto=Decimal('300.00'),
            descripcion='Venta',
            pedido=pedido,
            created_by=self.user
        )
        
        NotaCargo.objects.create(
            caja=self.caja_abierta,
            monto=Decimal('50.00'),
            motivo='Gastos limpieza',
            fecha=self.today,
            created_by=self.user
        )
        
        TransaccionCaja.objects.create(
            caja=self.caja_abierta,
            tipo_movimiento='egreso',
            monto=Decimal('50.00'),
            descripcion='Nota de Cargo',
            created_by=self.user
        )
        
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
        self.assertEqual(self.caja_abierta.ingresos, Decimal('300.00'))
        self.assertEqual(self.caja_abierta.egresos, Decimal('50.00'))
        self.assertEqual(self.caja_abierta.saldo_final, Decimal('1250.00'))  # 1000 + 300 - 50


class TransaccionCajaAPITest(APITestCase):
    """
    Tests for TransaccionCajaViewSet API
    """
    
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass',
            email='test@example.com'
        )
        
        # Create test store
        self.tienda = Tienda.objects.create(
            nombre='Tienda Central', 
            direccion='Calle Principal 123'
        )
        
        # Associate user with store
        self.user.tienda = self.tienda
        self.user.save()
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create cash register
        self.caja = Caja.objects.create(
            tienda=self.tienda,
            fecha=date.today(),
            fondo_inicial=Decimal('1000.00'),
            ingresos=Decimal('0.00'),
            egresos=Decimal('0.00'),
            saldo_final=Decimal('1000.00'),
            cerrada=False,
            created_by=self.user
        )
        
        # Create customer
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test', 
            tienda=self.tienda
        )
        
        # Create order
        self.pedido = Pedido.objects.create(
            cliente=self.cliente,
            fecha=make_aware(datetime.now()),
            estado='completado',
            total=Decimal('300.00'),
            tienda=self.tienda,
            tipo='venta',
            descuento_aplicado=Decimal('0.00')
        )
        
        # Create anticipo
        self.anticipo = Anticipo.objects.create(
            cliente=self.cliente,
            monto=Decimal('100.00'),
            fecha=date.today(),
            created_by=self.user
        )
        
        # Create nota de cargo
        self.nota_cargo = NotaCargo.objects.create(
            caja=self.caja,
            monto=Decimal('50.00'),
            motivo='Gastos limpieza',
            fecha=date.today(),
            created_by=self.user
        )
        
        # Create transactions
        self.transaccion_venta = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='ingreso',
            monto=Decimal('300.00'),
            descripcion='Venta',
            pedido=self.pedido,
            created_by=self.user
        )
        
        self.transaccion_anticipo = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='ingreso',
            monto=Decimal('100.00'),
            descripcion='Anticipo',
            anticipo=self.anticipo,
            created_by=self.user
        )
        
        self.transaccion_egreso = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='egreso',
            monto=Decimal('50.00'),
            descripcion='Nota de Cargo',
            nota_cargo=self.nota_cargo,
            created_by=self.user
        )
    
    def test_transaccion_caja_viewset_list(self):
        """Test list endpoint of TransaccionCajaViewSet"""
        url = reverse('transaccioncaja-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # should list all 3 transactions
        
        # Test filtering by caja
        response = self.client.get(f"{url}?caja={self.caja.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # Test filtering by tipo_movimiento
        response = self.client.get(f"{url}?tipo_movimiento=ingreso")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Test filtering by pedido
        response = self.client.get(f"{url}?pedido={self.pedido.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
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
        self.assertEqual(response.data['caja'], self.caja.pk)
    
    def test_transaccion_caja_viewset_update(self):
        """Test update endpoint of TransaccionCajaViewSet"""
        url = reverse('transaccioncaja-detail', kwargs={'pk': self.transaccion_venta.pk})
        data = {
            'caja': self.caja.pk,
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


class MovimientosCajaReporteAPITest(APITestCase):
    """
    Tests for MovimientosCajaReporteAPIView
    """
    
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass',
            email='test@example.com'
        )
        
        # Create test store
        self.tienda = Tienda.objects.create(
            nombre='Tienda Central', 
            direccion='Calle Principal 123'
        )
        
        # Associate user with store
        self.user.tienda = self.tienda
        self.user.save()
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Set dates
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
        
        # Create cash registers
        self.caja_today = Caja.objects.create(
            tienda=self.tienda,
            fecha=self.today,
            fondo_inicial=Decimal('1000.00'),
            ingresos=Decimal('400.00'),
            egresos=Decimal('50.00'),
            saldo_final=Decimal('1350.00'),
            cerrada=False,
            created_by=self.user
        )
        
        self.caja_yesterday = Caja.objects.create(
            tienda=self.tienda,
            fecha=self.yesterday,
            fondo_inicial=Decimal('800.00'),
            ingresos=Decimal('1200.00'),
            egresos=Decimal('300.00'),
            saldo_final=Decimal('1700.00'),
            cerrada=True,
            created_by=self.user
        )
        
        # Create customer
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test', 
            tienda=self.tienda
        )
        
        # Create order
        self.pedido = Pedido.objects.create(
            cliente=self.cliente,
            fecha=make_aware(datetime.now()),
            estado='completado',
            total=Decimal('300.00'),
            tienda=self.tienda,
            tipo='venta',
            descuento_aplicado=Decimal('0.00')
        )
        
        # Create transactions
        self.transaccion_venta = TransaccionCaja.objects.create(
            caja=self.caja_today,
            tipo_movimiento='ingreso',
            monto=Decimal('300.00'),
            descripcion='Venta',
            pedido=self.pedido,
            created_by=self.user
        )
        
        self.anticipo = Anticipo.objects.create(
            cliente=self.cliente,
            monto=Decimal('100.00'),
            fecha=self.today,
            created_by=self.user
        )
        
        self.transaccion_anticipo = TransaccionCaja.objects.create(
            caja=self.caja_today,
            tipo_movimiento='ingreso',
            monto=Decimal('100.00'),
            descripcion='Anticipo',
            anticipo=self.anticipo,
            created_by=self.user
        )
        
        self.nota_cargo = NotaCargo.objects.create(
            caja=self.caja_today,
            monto=Decimal('50.00'),
            motivo='Gastos limpieza',
            fecha=self.today,
            created_by=self.user
        )
        
        self.transaccion_egreso = TransaccionCaja.objects.create(
            caja=self.caja_today,
            tipo_movimiento='egreso',
            monto=Decimal('50.00'),
            descripcion='Nota de Cargo',
            nota_cargo=self.nota_cargo,
            created_by=self.user
        )    def test_movimientos_caja_reporte_api(self):
        """Test MovimientosCajaReporteAPIView"""
        url = reverse('movimientos-caja-reporte')
        
        # Test without filters
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check structure of the response (array of cajas with transactions)
        self.assertTrue(isinstance(response.data, list))
        self.assertEqual(len(response.data), 2)  # Both cajas (today and yesterday)
        
        # Test with store filter
        response = self.client.get(f"{url}?tienda_id={self.tienda.pk}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Both cajas are for the same tienda
        
        # Test with date filter
        response = self.client.get(f"{url}?fecha={self.today.isoformat()}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only today's caja
        
        # Check the data structure
        caja_data = response.data[0]
        self.assertEqual(caja_data['tienda_id'], self.tienda.pk)
        
        # The date format in the response could vary
        fecha_str = str(caja_data['fecha'])
        # Check that it contains today's date info
        self.assertTrue(str(self.today.year) in fecha_str)
        
        # Check transactions
        movimientos = caja_data['movimientos']
        self.assertEqual(len(movimientos), 3)  # All 3 transactions for today's caja
        
        # Verify the transactions data
        tipos_movimiento = [movimiento['tipo'] for movimiento in movimientos]
        self.assertEqual(tipos_movimiento.count('ingreso'), 2)
        self.assertEqual(tipos_movimiento.count('egreso'), 1)
        
        # Test with invalid date format
        response = self.client.get(f"{url}?fecha=invalid-date")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_movimientos_caja_reporte_filters(self):
        """Test additional filters in MovimientosCajaReporteAPIView"""
        url = reverse('movimientos-caja-reporte')
        
        # Create another cash register for another store
        tienda2 = Tienda.objects.create(nombre='Tienda 2', direccion='Otra dirección')
        caja_tienda2 = Caja.objects.create(
            tienda=tienda2,
            fecha=self.today,
            fondo_inicial=Decimal('500.00'),
            ingresos=Decimal('0.00'),
            egresos=Decimal('0.00'),
            saldo_final=Decimal('500.00'),
            cerrada=False,
            created_by=self.user
        )
        
        # Test filtering by tienda_id
        response = self.client.get(f"{url}?tienda_id={tienda2.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only the new store's caja
        self.assertEqual(response.data[0]['tienda_id'], tienda2.pk)
        
        # Test valid date range
        response = self.client.get(f"{url}?fecha={self.yesterday.isoformat()}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only yesterday's caja
        
        # Verify the response reflects the correct caja
        caja_data = response.data[0]
        self.assertEqual(caja_data['fecha'], self.yesterday.isoformat())
        self.assertEqual(caja_data['fondo_inicial'], '800.00')
          def test_movimientos_caja_reporte_validation(self):
        """Test validations in MovimientosCajaReporteAPIView"""
        url = reverse('movimientos-caja-reporte')
        
        # Test invalid date format
        response = self.client.get(f"{url}?fecha=2023-13-32")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Test non-existent tienda filter (should not cause error, just empty results)
        response = self.client.get(f"{url}?tienda_id=9999")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No cajas for non-existent tienda
        
        # Check that it contains today's date info
        self.assertTrue(str(self.today.year) in fecha_str)
        
        # Check transactions
        movimientos = caja_data['movimientos']
        self.assertEqual(len(movimientos), 3)
        
        # Test with invalid date format
        response = self.client.get(f"{url}?fecha=invalid-date")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
