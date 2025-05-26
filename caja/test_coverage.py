"""
Tests to improve coverage of the caja module
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

User = get_user_model()

class CajaViewsTestCase(TestCase):
    """Tests for frontend views in caja app"""
    
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass')
        
        # Create test stores
        self.tienda1 = Tienda.objects.create(
            nombre='Tienda Central', 
            direccion='Calle Principal 123'
        )
        self.tienda2 = Tienda.objects.create(
            nombre='Tienda Sucursal', 
            direccion='Av. Secundaria 456'
        )
        
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
        
        # Create closed cash register for today
        self.caja_cerrada = Caja.objects.create(
            tienda=self.tienda2,
            fecha=self.today,
            fondo_inicial=Decimal('500.00'),
            ingresos=Decimal('1500.00'),
            egresos=Decimal('200.00'),
            saldo_final=Decimal('1800.00'),
            cerrada=True,
            created_by=self.user
        )
        
        # Create yesterday's cash register (closed)
        self.caja_ayer = Caja.objects.create(
            tienda=self.tienda1,
            fecha=self.yesterday,
            fondo_inicial=Decimal('800.00'),
            ingresos=Decimal('1200.00'),
            egresos=Decimal('300.00'),
            saldo_final=Decimal('1700.00'),
            cerrada=True,
            created_by=self.user
        )
        
        # Create test customer and order
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test', 
            tienda=self.tienda1
        )
        self.pedido = Pedido.objects.create(
            cliente=self.cliente,
            fecha=make_aware(datetime.now()),
            estado='completado',
            total=Decimal('300.00'),
            tienda=self.tienda1,
            tipo='venta',
            descuento_aplicado=Decimal('0.00')
        )
        
        # Create advance payment
        self.anticipo = Anticipo.objects.create(
            cliente=self.cliente,
            monto=Decimal('100.00'),
            fecha=self.today,
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
        
        # Create invoice
        self.factura = Factura.objects.create(
            pedido=self.pedido,
            folio='F001',
            fecha=self.today,
            total=Decimal('300.00'),
            created_by=self.user
        )
        
        # Create transactions
        self.transaccion_ingreso = TransaccionCaja.objects.create(
            caja=self.caja_abierta,
            tipo_movimiento='ingreso',
            monto=Decimal('300.00'),
            descripcion='Venta',
            pedido=self.pedido,
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
        
        self.transaccion_egreso = TransaccionCaja.objects.create(
            caja=self.caja_abierta,
            tipo_movimiento='egreso',
            monto=Decimal('50.00'),
            descripcion='Nota de Cargo',
            nota_cargo=self.nota_cargo,
            created_by=self.user
        )
    
    def test_caja_list_view(self):
        """Test caja_list view displays cash registers correctly"""
        url = reverse('caja:lista')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/caja_list.html')
        
        # Check today's cash registers are shown
        cajas = response.context['cajas']
        self.assertEqual(len(cajas), 2)
        
        # Test filter by store
        response = self.client.get(f"{url}?tienda={self.tienda1.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['cajas']), 1)
        
        # Test view history
        response = self.client.get(f"{url}?historial=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['cajas']), 3)
        
        # Test filter by date
        response = self.client.get(f"{url}?fecha={self.yesterday.isoformat()}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['cajas']), 1)
    
    def test_abrir_caja_view(self):
        """Test abrir_caja view opens a cash register correctly"""
        url = reverse('caja:abrir')
        
        # Test GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/caja_form.html')
        
        # Test POST with valid data
        nueva_tienda = Tienda.objects.create(
            nombre='Nueva Tienda', 
            direccion='Calle Nueva 789'
        )
        data = {
            'tienda': nueva_tienda.pk,
            'fondo_inicial': '1500.00',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('caja:lista'))
        
        # Verify cash register was created
        self.assertTrue(Caja.objects.filter(
            tienda=nueva_tienda, 
            fecha=self.today, 
            cerrada=False
        ).exists())
        
        # Test POST when cash register already exists
        response = self.client.post(url, {
            'tienda': self.tienda1.pk,
            'fondo_inicial': '1000.00',
        })
        self.assertRedirects(response, reverse('caja:lista'))
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Ya existe una caja abierta' in str(m) for m in messages))
        
        # Test POST with missing store
        response = self.client.post(url, {
            'tienda': '',
            'fondo_inicial': '1000.00',
        })
        self.assertRedirects(response, reverse('caja:abrir'))
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Debe seleccionar una tienda' in str(m) for m in messages))
    
    def test_cerrar_caja_view(self):
        """Test cerrar_caja view closes a cash register correctly"""
        url = reverse('caja:cerrar', kwargs={'pk': self.caja_abierta.pk})
        
        # Test GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/caja_cierre.html')
        
        # Check context data
        self.assertEqual(response.context['caja'], self.caja_abierta)
        self.assertEqual(response.context['total_ingresos'], Decimal('400.00'))
        self.assertEqual(response.context['total_egresos'], Decimal('50.00'))
        self.assertEqual(response.context['saldo_actual'], Decimal('1350.00'))
        
        # Test POST (close cash register)
        response = self.client.post(url)
        self.assertRedirects(response, reverse('caja:lista'))
        
        # Verify cash register was closed
        self.caja_abierta.refresh_from_db()
        self.assertTrue(self.caja_abierta.cerrada)
        self.assertEqual(self.caja_abierta.ingresos, Decimal('400.00'))
        self.assertEqual(self.caja_abierta.egresos, Decimal('50.00'))
        self.assertEqual(self.caja_abierta.saldo_final, Decimal('1350.00'))
    
    def test_movimientos_list_view(self):
        """Test movimientos_list view displays transactions correctly"""
        url = reverse('caja:movimientos')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/movimientos_list.html')
        
        # Check all transactions are shown
        self.assertEqual(len(response.context['movimientos']), 3)
        
        # Test filter by type
        response = self.client.get(f"{url}?tipo=ingreso")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['movimientos']), 2)
        
        # Test filter by store
        response = self.client.get(f"{url}?tienda={self.tienda1.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['movimientos']), 3)
        
        # Test filter by date
        response = self.client.get(f"{url}?fecha_desde={self.today.isoformat()}&fecha_hasta={self.today.isoformat()}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['movimientos']), 3)
    
    def test_nota_cargo_create_view(self):
        """Test nota_cargo_create view creates charge notes correctly"""
        url = reverse('caja:nueva_nota_cargo')
        
        # Test GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/nota_cargo_form.html')
        
        # Test POST with valid data
        data = {
            'caja': self.caja_abierta.pk,
            'monto': '75.50',
            'motivo': 'Compra de material de oficina',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('caja:movimientos'))
        
        # Verify charge note was created
        self.assertTrue(NotaCargo.objects.filter(
            motivo='Compra de material de oficina'
        ).exists())
        
        # Verify transaction was created
        nueva_nota = NotaCargo.objects.get(motivo='Compra de material de oficina')
        self.assertTrue(TransaccionCaja.objects.filter(
            nota_cargo=nueva_nota
        ).exists())
        
        # Test POST with invalid data (no reason)
        response = self.client.post(url, {
            'caja': self.caja_abierta.pk,
            'monto': '50.00',
            'motivo': '',
        })
        self.assertRedirects(response, url)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('Caja y motivo son obligatorios' in str(m) for m in messages))
        
        # Test POST with invalid amount
        response = self.client.post(url, {
            'caja': self.caja_abierta.pk,
            'monto': '0',
            'motivo': 'Prueba',
        })
        self.assertRedirects(response, url)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any('El monto debe ser mayor a cero' in str(m) for m in messages))


class CajaAPITestCase(APITestCase):
    """Tests for API endpoints in caja app"""
    
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass',
            email='test@example.com'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test store
        self.tienda = Tienda.objects.create(
            nombre='Tienda Central', 
            direccion='Calle Principal 123'
        )
        
        # Set dates
        self.today = date.today()
        
        # Create cash register
        self.caja = Caja.objects.create(
            tienda=self.tienda,
            fecha=self.today,
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
    
    def test_caja_viewset_basic_operations(self):
        """Test basic CRUD operations for CajaViewSet"""
        # Test list
        url = reverse('caja-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test retrieve
        url = reverse('caja-detail', kwargs={'pk': self.caja.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tienda'], self.tienda.pk)
        
        # Test create
        url = reverse('caja-list')
        data = {
            'tienda': self.tienda.pk,
            'fecha': (self.today + timedelta(days=1)).isoformat(),
            'fondo_inicial': '2000.00',
            'ingresos': '0.00',
            'egresos': '0.00',
            'saldo_final': '2000.00',
            'cerrada': False
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Caja.objects.count(), 2)
        
        # Test update
        url = reverse('caja-detail', kwargs={'pk': self.caja.pk})
        data = {
            'tienda': self.tienda.pk,
            'fecha': self.today.isoformat(),
            'fondo_inicial': '1500.00',  # Changed
            'ingresos': '0.00',
            'egresos': '0.00',
            'saldo_final': '1500.00',  # Changed
            'cerrada': False
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.caja.refresh_from_db()
        self.assertEqual(self.caja.fondo_inicial, Decimal('1500.00'))
    
    def test_caja_abrir_action(self):
        """Test abrir_caja custom action"""
        # Delete existing cash register to test creating a new one
        self.caja.delete()
        
        url = reverse('caja-abrir-caja')
        data = {
            'tienda_id': self.tienda.pk,
            'fondo_inicial': '1500.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Caja.objects.filter(
            tienda=self.tienda, 
            fecha=self.today, 
            cerrada=False
        ).exists())
        
        # Test with invalid data (missing tienda_id)
        response = self.client.post(url, {
            'fondo_inicial': '1500.00'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test when cash register already exists
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
    
    def test_caja_cerrar_action(self):
        """Test cerrar_caja custom action"""
        # Create a transaction for the cash register
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            fecha=make_aware(datetime.now()),
            estado='completado',
            total=Decimal('300.00'),
            tienda=self.tienda,
            tipo='venta',
            descuento_aplicado=Decimal('0.00')
        )
        
        TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='ingreso',
            monto=Decimal('300.00'),
            descripcion='Venta',
            pedido=pedido,
            created_by=self.user
        )
        
        url = reverse('caja-cerrar-caja')
        data = {
            'tienda_id': self.tienda.pk,
            'fecha': self.today.isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cash register was closed
        self.caja.refresh_from_db()
        self.assertTrue(self.caja.cerrada)
        self.assertEqual(self.caja.ingresos, Decimal('300.00'))
        
        # Test with invalid data (missing tienda_id)
        url = reverse('caja-cerrar-caja')
        response = self.client.post(url, {
            'fecha': self.today.isoformat()
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with invalid date format
        url = reverse('caja-cerrar-caja')
        response = self.client.post(url, {
            'tienda_id': self.tienda.pk,
            'fecha': 'invalid-date'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_transaccion_caja_viewset(self):
        """Test TransaccionCajaViewSet"""
        # Create a transaction
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            fecha=make_aware(datetime.now()),
            estado='completado',
            total=Decimal('300.00'),
            tienda=self.tienda,
            tipo='venta',
            descuento_aplicado=Decimal('0.00')
        )
        
        transaccion = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='ingreso',
            monto=Decimal('300.00'),
            descripcion='Venta',
            pedido=pedido,
            created_by=self.user
        )
          # Test list
        url = reverse('transacciones_caja-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
          # Test retrieve
        url = reverse('transacciones_caja-detail', kwargs={'pk': transaccion.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['monto'], '300.00')
        
        # Test filter by caja
        url = reverse('transacciones_caja-list') + f'?caja={self.caja.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
          # Test filter by tipo_movimiento
        url = reverse('transacciones_caja-list') + '?tipo_movimiento=ingreso'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_movimientos_caja_reporte_api(self):
        """Test MovimientosCajaReporteAPIView"""
        # Create transactions
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            fecha=make_aware(datetime.now()),
            estado='completado',
            total=Decimal('300.00'),
            tienda=self.tienda,
            tipo='venta',
            descuento_aplicado=Decimal('0.00')
        )
        
        TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='ingreso',
            monto=Decimal('300.00'),
            descripcion='Venta',
            pedido=pedido,
            created_by=self.user
        )
        
        anticipo = Anticipo.objects.create(
            cliente=self.cliente,
            monto=Decimal('100.00'),
            fecha=self.today,
            created_by=self.user
        )
        
        TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='ingreso',
            monto=Decimal('100.00'),
            descripcion='Anticipo',
            anticipo=anticipo,
            created_by=self.user
        )
        
        # Test report without filters
        url = reverse('movimientos-caja-reporte')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # 1 cash register
        
        # Check cash register data
        caja_data = response.data[0]
        self.assertEqual(caja_data['tienda_id'], self.tienda.pk)
        self.assertEqual(caja_data['fecha'], self.today.isoformat())
        self.assertEqual(len(caja_data['movimientos']), 2)  # 2 transactions
        
        # Test filter by tienda
        url = reverse('movimientos-caja-reporte') + f'?tienda_id={self.tienda.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test filter by fecha
        url = reverse('movimientos-caja-reporte') + f'?fecha={self.today.isoformat()}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # Test with invalid date
        url = reverse('movimientos-caja-reporte') + '?fecha=invalid-date'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
