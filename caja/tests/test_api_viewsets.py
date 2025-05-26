"""
Pruebas automáticas para los viewsets API de caja:
- CajaViewSet: Acciones personalizadas (abrir_caja, cerrar_caja)
- TransaccionCajaViewSet: Creación y validación de transacciones
- MovimientosCajaReporteAPIView: Generación de reportes
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from caja.models import Caja, NotaCargo, Factura, TransaccionCaja
from tiendas.models import Tienda
from ventas.models import Pedido
from clientes.models import Cliente, Anticipo
from datetime import date, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.timezone import make_aware
from datetime import datetime

User = get_user_model()

class CajaViewSetCustomActionsTestCase(APITestCase):
    def setUp(self):
        # Create user and authenticate
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test@example.com')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test tiendas
        self.tienda1 = Tienda.objects.create(nombre='Tienda Central', direccion='Calle Principal 123')
        self.tienda2 = Tienda.objects.create(nombre='Tienda Sucursal', direccion='Av. Secundaria 456')
        
        # Create caja for testing cerrar_caja action
        self.today = date.today()
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
        
        # Create transacciones for the open caja
        self.cliente = Cliente.objects.create(nombre='Cliente Test', tienda=self.tienda1)
        self.pedido = Pedido.objects.create(
            cliente=self.cliente, 
            fecha=make_aware(datetime.now()),
            estado='completado', 
            total=Decimal('300.00'),
            tienda=self.tienda1,
            tipo='venta',
            descuento_aplicado=Decimal('0.00')
        )
        
        self.transaccion_ingreso = TransaccionCaja.objects.create(
            caja=self.caja_abierta,
            tipo_movimiento='ingreso',
            monto=Decimal('300.00'),
            descripcion='Venta',
            pedido=self.pedido,
            created_by=self.user
        )
        
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
            descripcion='Nota de Cargo: Gastos de limpieza',
            nota_cargo=self.nota_cargo,
            created_by=self.user
        )

    def test_abrir_caja_action_success(self):
        """Test que la acción abrir_caja crea una caja correctamente"""
        url = reverse('caja-abrir-caja')
        data = {
            'tienda_id': self.tienda2.id,  # Tienda sin caja abierta
            'fondo_inicial': 1500.00
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['tienda'], self.tienda2.id)
        self.assertEqual(Decimal(response.data['fondo_inicial']), Decimal('1500.00'))
        self.assertEqual(Decimal(response.data['saldo_final']), Decimal('1500.00'))
        self.assertFalse(response.data['cerrada'])
        
        # Verificar que se creó en la BD
        self.assertTrue(Caja.objects.filter(tienda=self.tienda2, fecha=self.today, cerrada=False).exists())

    def test_abrir_caja_action_tienda_no_existe(self):
        """Test que la acción abrir_caja valida que la tienda exista"""
        url = reverse('caja-abrir-caja')
        data = {
            'tienda_id': 9999,  # ID que no existe
            'fondo_inicial': 1000.00
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('Tienda no encontrada', response.data['error'])

    def test_abrir_caja_action_caja_ya_abierta(self):
        """Test que la acción abrir_caja valida que no exista una caja abierta para la tienda"""
        url = reverse('caja-abrir-caja')
        data = {
            'tienda_id': self.tienda1.id,  # Esta tienda ya tiene una caja abierta
            'fondo_inicial': 1000.00
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response.data)
        self.assertIn('Ya existe una caja abierta', response.data['error'])

    def test_abrir_caja_action_datos_incompletos(self):
        """Test que la acción abrir_caja valida datos requeridos"""
        url = reverse('caja-abrir-caja')
        data = {
            'tienda_id': self.tienda2.id,
            # Falta fondo_inicial
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_cerrar_caja_action_success(self):
        """Test que la acción cerrar_caja cierra una caja correctamente"""
        url = reverse('caja-cerrar-caja')
        data = {
            'tienda_id': self.tienda1.id,
            'fecha': self.today.isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tienda'], self.tienda1.id)
        self.assertTrue(response.data['cerrada'])
        self.assertEqual(Decimal(response.data['ingresos']), Decimal('300.00'))
        self.assertEqual(Decimal(response.data['egresos']), Decimal('50.00'))
        self.assertEqual(Decimal(response.data['saldo_final']), Decimal('1250.00'))  # 1000 + 300 - 50
        
        # Verificar que se actualizó en la BD
        self.caja_abierta.refresh_from_db()
        self.assertTrue(self.caja_abierta.cerrada)
        self.assertEqual(self.caja_abierta.ingresos, Decimal('300.00'))
        self.assertEqual(self.caja_abierta.egresos, Decimal('50.00'))
        self.assertEqual(self.caja_abierta.saldo_final, Decimal('1250.00'))

    def test_cerrar_caja_action_caja_no_existe(self):
        """Test que la acción cerrar_caja valida que la caja exista"""
        # Crear una fecha para la que no hay caja
        fecha_sin_caja = self.today - timedelta(days=7)
        
        url = reverse('caja-cerrar-caja')
        data = {
            'tienda_id': self.tienda1.id,
            'fecha': fecha_sin_caja.isoformat()
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('Caja no encontrada', response.data['error'])

    def test_cerrar_caja_action_formato_fecha_invalido(self):
        """Test que la acción cerrar_caja valida el formato de fecha"""
        url = reverse('caja-cerrar-caja')
        data = {
            'tienda_id': self.tienda1.id,
            'fecha': '01/01/2025'  # Formato incorrecto
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Formato de fecha inválido', response.data['error'])

class TransaccionCajaViewSetTestCase(APITestCase):
    def setUp(self):
        # Create user with tienda association
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test@example.com')
        self.tienda = Tienda.objects.create(nombre='Tienda Central', direccion='Calle Principal 123')
        # Simular relación user-tienda (normalmente mediante perfil o directamente en User model)
        self.user.tienda = self.tienda
        self.user.save()
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create caja abierta
        self.today = date.today()
        self.caja_abierta = Caja.objects.create(
            tienda=self.tienda,
            fecha=self.today,
            fondo_inicial=Decimal('1000.00'),
            ingresos=Decimal('0.00'),
            egresos=Decimal('0.00'),
            saldo_final=Decimal('1000.00'),
            cerrada=False,
            created_by=self.user
        )
        
        # Create test cliente and pedido
        self.cliente = Cliente.objects.create(nombre='Cliente Test', tienda=self.tienda)
        self.pedido = Pedido.objects.create(
            cliente=self.cliente, 
            fecha=make_aware(datetime.now()),
            estado='completado', 
            total=Decimal('300.00'),
            tienda=self.tienda,
            tipo='venta',
            descuento_aplicado=Decimal('0.00')
        )

    def test_create_transaccion_success(self):
        """Test que se puede crear una transacción correctamente"""
        url = reverse('transaccioncaja-list')
        data = {
            'tipo_movimiento': 'ingreso',
            'monto': '300.00',
            'descripcion': 'Venta de producto',
            'pedido': self.pedido.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['caja'], self.caja_abierta.id)
        self.assertEqual(response.data['tipo_movimiento'], 'ingreso')
        self.assertEqual(Decimal(response.data['monto']), Decimal('300.00'))
        self.assertEqual(response.data['pedido'], self.pedido.id)

    def test_perform_create_assigns_caja_and_user(self):
        """Test que perform_create asigna la caja abierta y el usuario correctamente"""
        url = reverse('transaccioncaja-list')
        data = {
            'tipo_movimiento': 'egreso',
            'monto': '50.00',
            'descripcion': 'Gastos varios'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que se asignó la caja y el usuario
        transaccion = TransaccionCaja.objects.get(id=response.data['id'])
        self.assertEqual(transaccion.caja, self.caja_abierta)
        self.assertEqual(transaccion.created_by, self.user)

    def test_list_transacciones_with_filters(self):
        """Test que se pueden listar transacciones con filtros"""
        # Crear algunas transacciones
        TransaccionCaja.objects.create(
            caja=self.caja_abierta,
            tipo_movimiento='ingreso',
            monto=Decimal('300.00'),
            descripcion='Venta',
            pedido=self.pedido,
            created_by=self.user
        )
        
        TransaccionCaja.objects.create(
            caja=self.caja_abierta,
            tipo_movimiento='egreso',
            monto=Decimal('50.00'),
            descripcion='Gastos varios',
            created_by=self.user
        )
        
        # Listar sin filtros
        url = reverse('transaccioncaja-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Filtrar por tipo_movimiento
        url = reverse('transaccioncaja-list') + '?tipo_movimiento=ingreso'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['tipo_movimiento'], 'ingreso')
        
        # Filtrar por caja
        url = reverse('transaccioncaja-list') + f'?caja={self.caja_abierta.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_transaccion_sin_caja_abierta(self):
        """Test que no se puede crear una transacción si no hay caja abierta"""
        # Cerrar la caja
        self.caja_abierta.cerrada = True
        self.caja_abierta.save()
        
        url = reverse('transaccioncaja-list')
        data = {
            'tipo_movimiento': 'ingreso',
            'monto': '300.00',
            'descripcion': 'Venta de producto',
            'pedido': self.pedido.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No hay una caja abierta', str(response.data))

class MovimientosCajaReporteAPIViewTestCase(APITestCase):
    def setUp(self):
        # Create user and authenticate
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test@example.com')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create test tiendas
        self.tienda1 = Tienda.objects.create(nombre='Tienda Central', direccion='Calle Principal 123')
        self.tienda2 = Tienda.objects.create(nombre='Tienda Sucursal', direccion='Av. Secundaria 456')
        
        # Create cajas for different dates
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
        
        # Caja for tienda1 today
        self.caja1_today = Caja.objects.create(
            tienda=self.tienda1,
            fecha=self.today,
            fondo_inicial=Decimal('1000.00'),
            ingresos=Decimal('500.00'),
            egresos=Decimal('200.00'),
            saldo_final=Decimal('1300.00'),
            cerrada=True,
            created_by=self.user
        )
        
        # Caja for tienda2 today
        self.caja2_today = Caja.objects.create(
            tienda=self.tienda2,
            fecha=self.today,
            fondo_inicial=Decimal('800.00'),
            ingresos=Decimal('300.00'),
            egresos=Decimal('100.00'),
            saldo_final=Decimal('1000.00'),
            cerrada=True,
            created_by=self.user
        )
        
        # Caja for tienda1 yesterday
        self.caja1_yesterday = Caja.objects.create(
            tienda=self.tienda1,
            fecha=self.yesterday,
            fondo_inicial=Decimal('900.00'),
            ingresos=Decimal('400.00'),
            egresos=Decimal('150.00'),
            saldo_final=Decimal('1150.00'),
            cerrada=True,
            created_by=self.user
        )
        
        # Create transacciones for caja1_today
        self.cliente = Cliente.objects.create(nombre='Cliente Test', tienda=self.tienda1)
        self.pedido = Pedido.objects.create(
            cliente=self.cliente, 
            fecha=make_aware(datetime.now()),
            estado='completado', 
            total=Decimal('300.00'),
            tienda=self.tienda1,
            tipo='venta',
            descuento_aplicado=Decimal('0.00')
        )
        
        self.transaccion_ingreso = TransaccionCaja.objects.create(
            caja=self.caja1_today,
            tipo_movimiento='ingreso',
            monto=Decimal('300.00'),
            descripcion='Venta',
            pedido=self.pedido,
            created_by=self.user
        )
        
        self.nota_cargo = NotaCargo.objects.create(
            caja=self.caja1_today,
            monto=Decimal('100.00'),
            motivo='Gastos varios',
            fecha=self.today,
            created_by=self.user
        )
        
        self.transaccion_egreso = TransaccionCaja.objects.create(
            caja=self.caja1_today,
            tipo_movimiento='egreso',
            monto=Decimal('100.00'),
            descripcion='Nota de Cargo: Gastos varios',
            nota_cargo=self.nota_cargo,
            created_by=self.user
        )
          # Create anticipo for cliente
        self.anticipo = Anticipo.objects.create(
            cliente=self.cliente,            monto=Decimal('200.00'),
            fecha=self.today,
            created_by=self.user
        )
        
        self.transaccion_anticipo = TransaccionCaja.objects.create(
            caja=self.caja1_today,
            tipo_movimiento='ingreso',
            monto=Decimal('200.00'),
            descripcion='Anticipo',
            anticipo=self.anticipo,
            created_by=self.user
        )
        
    def test_get_reporte_sin_filtros(self):
        """Test que el reporte devuelve todas las cajas con sus movimientos"""
        url = reverse('movimientos-caja-reporte')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # 3 cajas
        
        # Verificar estructura del reporte
        for caja_data in response.data:
            self.assertIn('tienda_id', caja_data)
            self.assertIn('tienda_nombre', caja_data)
            self.assertIn('fecha', caja_data)
            self.assertIn('fondo_inicial', caja_data)
            self.assertIn('ingresos_totales', caja_data)
            self.assertIn('egresos_totales', caja_data)
            self.assertIn('saldo_final', caja_data)
            self.assertIn('movimientos', caja_data)
            
            # Si es la caja1_today, verificar movimientos
            if caja_data['tienda_id'] == self.tienda1.id and caja_data['fecha'] == self.today.isoformat():
                self.assertEqual(len(caja_data['movimientos']), 3)  # 3 transacciones

    def test_get_reporte_filtro_tienda(self):
        """Test que el reporte se puede filtrar por tienda"""
        url = reverse('caja-reporte') + f'?tienda_id={self.tienda1.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 2 cajas de tienda1
        
        # Verificar que todas las cajas son de tienda1
        for caja_data in response.data:
            self.assertEqual(caja_data['tienda_id'], self.tienda1.id)
            self.assertEqual(caja_data['tienda_nombre'], self.tienda1.nombre)

    def test_get_reporte_filtro_fecha(self):
        """Test que el reporte se puede filtrar por fecha"""
        url = reverse('caja-reporte') + f'?fecha={self.today.isoformat()}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # 2 cajas de hoy
        
        # Verificar que todas las cajas son de hoy
        for caja_data in response.data:
            self.assertEqual(caja_data['fecha'], self.today.isoformat())

    def test_get_reporte_formato_fecha_invalido(self):
        """Test que el reporte valida el formato de fecha"""
        url = reverse('caja-reporte') + '?fecha=01/01/2025'  # Formato incorrecto
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Formato de fecha inválido', response.data['error'])

    def test_get_reporte_detalles_movimientos(self):
        """Test que el reporte incluye detalles correctos de los movimientos"""
        url = reverse('caja-reporte') + f'?tienda_id={self.tienda1.id}&fecha={self.today.isoformat()}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # 1 caja
        
        caja_data = response.data[0]
        self.assertEqual(len(caja_data['movimientos']), 3)  # 3 transacciones
        
        # Verificar descripciones enriquecidas
        for movimiento in caja_data['movimientos']:
            if 'Venta Pedido' in movimiento['descripcion']:
                self.assertIn(str(self.pedido.id), movimiento['descripcion'])
                self.assertEqual(movimiento['tipo'], 'ingreso')
                self.assertEqual(Decimal(movimiento['monto']), Decimal('300.00'))
            elif 'Nota de Cargo' in movimiento['descripcion']:
                self.assertIn(str(self.nota_cargo.id), movimiento['descripcion'])
                self.assertIn(self.nota_cargo.motivo, movimiento['descripcion'])
                self.assertEqual(movimiento['tipo'], 'egreso')
                self.assertEqual(Decimal(movimiento['monto']), Decimal('100.00'))
            elif 'Anticipo Cliente' in movimiento['descripcion']:
                self.assertIn(str(self.cliente.id), movimiento['descripcion'])
                self.assertEqual(movimiento['tipo'], 'ingreso')
                self.assertEqual(Decimal(movimiento['monto']), Decimal('200.00'))
