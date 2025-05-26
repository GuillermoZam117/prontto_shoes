"""
Pruebas unitarias para mejorar la cobertura del módulo caja
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
from datetime import date, datetime
from django.utils.timezone import make_aware

User = get_user_model()

class CajaViewsTest(TestCase):
    """Pruebas para las vistas frontend del módulo caja"""
    
    def setUp(self):
        # Crear usuario de prueba
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')
        
        # Crear tiendas de prueba
        self.tienda1 = Tienda.objects.create(nombre='Tienda Central', direccion='Calle Principal 123')
        self.tienda2 = Tienda.objects.create(nombre='Tienda Sucursal', direccion='Av. Secundaria 456')
        
        # Fechas de prueba
        self.today = date.today()
        
        # Crear caja abierta
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
        
        # Crear caja cerrada
        self.caja_cerrada = Caja.objects.create(
            tienda=self.tienda2,
            fecha=self.today,
            fondo_inicial=Decimal('500.00'),
            ingresos=Decimal('2000.00'),
            egresos=Decimal('300.00'),
            saldo_final=Decimal('2200.00'),
            cerrada=True,
            created_by=self.user
        )
        
        # Crear cliente y pedido
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
        
        # Crear anticipo
        self.anticipo = Anticipo.objects.create(
            cliente=self.cliente,
            monto=Decimal('100.00'),
            fecha=self.today,
            created_by=self.user
        )
        
        # Crear nota de cargo
        self.nota_cargo = NotaCargo.objects.create(
            caja=self.caja_abierta,
            monto=Decimal('50.00'),
            motivo='Gastos de limpieza',
            fecha=self.today,
            created_by=self.user
        )
        
        # Crear factura
        self.factura = Factura.objects.create(
            pedido=self.pedido,
            folio='F001',
            fecha=self.today,
            total=Decimal('300.00'),
            created_by=self.user
        )
    
    def test_caja_list_view(self):
        """Prueba para la vista de listado de cajas"""
        url = reverse('caja:lista')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/caja_list.html')
        
        # Verificar que se muestran las cajas del día
        cajas = response.context['cajas']
        self.assertEqual(len(cajas), 2)
        
        # Probar filtro por tienda
        response = self.client.get(f"{url}?tienda={self.tienda1.pk}")
        self.assertEqual(response.status_code, 200)
        cajas_filtradas = response.context['cajas']
        self.assertEqual(len(cajas_filtradas), 1)
        self.assertEqual(cajas_filtradas[0].tienda, self.tienda1)
    
    def test_abrir_caja_view(self):
        """Prueba para la vista de apertura de caja"""
        url = reverse('caja:abrir')
        
        # Probar GET
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/caja_form.html')
        
        # Probar POST con datos válidos
        nueva_tienda = Tienda.objects.create(nombre='Nueva Tienda', direccion='Calle Nueva 789')
        data = {
            'tienda': nueva_tienda.pk,
            'fondo_inicial': '1500.00',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('caja:lista'))
        
        # Verificar que se creó la caja
        self.assertTrue(Caja.objects.filter(tienda=nueva_tienda, fecha=self.today, cerrada=False).exists())
    
    def test_cerrar_caja_view(self):
        """Prueba para la vista de cierre de caja"""
        # Crear transacciones para la caja
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
            descripcion='Nota de Cargo',
            nota_cargo=self.nota_cargo,
            created_by=self.user
        )
        
        # Probar GET
        url = reverse('caja:cerrar', args=[self.caja_abierta.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/caja_cierre.html')
        
        # Probar POST para cerrar caja
        response = self.client.post(url)
        self.assertRedirects(response, reverse('caja:lista'))
        
        # Verificar que la caja se cerró
        self.caja_abierta.refresh_from_db()
        self.assertTrue(self.caja_abierta.cerrada)
        self.assertEqual(self.caja_abierta.ingresos, Decimal('300.00'))
        self.assertEqual(self.caja_abierta.egresos, Decimal('50.00'))
    
    def test_movimientos_list_view(self):
        """Prueba para la vista de listado de movimientos"""
        # Crear transacciones
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
            descripcion='Nota de Cargo',
            nota_cargo=self.nota_cargo,
            created_by=self.user
        )
        
        url = reverse('caja:movimientos')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/movimientos_list.html')
        
        # Verificar movimientos en contexto
        movimientos = response.context['movimientos']
        self.assertEqual(len(movimientos), 2)
        
        # Probar filtro por tipo
        response = self.client.get(f"{url}?tipo=ingreso")
        self.assertEqual(response.status_code, 200)
        movimientos = response.context['movimientos']
        self.assertEqual(len(movimientos), 1)
        self.assertEqual(movimientos[0].tipo_movimiento, 'ingreso')

class CajaAPITest(APITestCase):
    """Pruebas para los endpoints API del módulo caja"""
    
    def setUp(self):
        # Crear usuario de prueba
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Crear tiendas de prueba
        self.tienda1 = Tienda.objects.create(nombre='Tienda Central', direccion='Calle Principal 123')
        
        # Fechas de prueba
        self.today = date.today()
        
        # Crear caja
        self.caja = Caja.objects.create(
            tienda=self.tienda1,
            fecha=self.today,
            fondo_inicial=Decimal('1000.00'),
            ingresos=Decimal('0.00'),
            egresos=Decimal('0.00'),
            saldo_final=Decimal('1000.00'),
            cerrada=False,
            created_by=self.user
        )
    
    def test_caja_list(self):
        """Prueba para listar cajas a través de la API"""
        url = reverse('caja-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
    
    def test_caja_create(self):
        """Prueba para crear una caja a través de la API"""
        url = reverse('caja-list')
        data = {
            'tienda': self.tienda1.pk,
            'fecha': (self.today.isoformat()),
            'fondo_inicial': '2000.00',
            'ingresos': '0.00',
            'egresos': '0.00',
            'saldo_final': '2000.00',
            'cerrada': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Caja.objects.count(), 2)
        
    def test_caja_detail(self):
        """Prueba para obtener detalle de una caja a través de la API"""
        url = reverse('caja-detail', args=[self.caja.pk])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['tienda'], self.tienda1.pk)
        self.assertEqual(response.data['fondo_inicial'], '1000.00')
      def test_caja_abrir_action(self):
        """Prueba para la acción personalizada abrir_caja"""
        # Primero eliminamos la caja existente para probar crear una nueva
        self.caja.delete()
        
        url = reverse('caja-abrir-caja')
        data = {
            'tienda_id': self.tienda1.pk,
            'fondo_inicial': '1500.00'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Caja.objects.filter(tienda=self.tienda1, fecha=self.today, cerrada=False).exists())
        nueva_caja = Caja.objects.get(tienda=self.tienda1, fecha=self.today)
        self.assertEqual(nueva_caja.fondo_inicial, Decimal('1500.00'))
          def test_caja_cerrar_action(self):
        """Prueba para la acción personalizada cerrar_caja"""
        # Crear transacciones para la caja
        cliente = Cliente.objects.create(nombre='Cliente Test', tienda=self.tienda1)
        pedido = Pedido.objects.create(
            cliente=cliente,
            fecha=make_aware(datetime.now()),
            estado='completado',
            total=Decimal('300.00'),
            tienda=self.tienda1,
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
            'tienda_id': self.tienda1.pk,
            'fecha': self.today.isoformat()
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que la caja se cerró
        self.caja.refresh_from_db()
        self.assertTrue(self.caja.cerrada)
        self.assertEqual(self.caja.ingresos, Decimal('300.00'))
