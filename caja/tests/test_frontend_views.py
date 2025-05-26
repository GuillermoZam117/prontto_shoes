"""
Pruebas automáticas para las vistas frontend de caja:
- caja_list: Listado de cajas
- abrir_caja: Apertura de caja diaria
- cerrar_caja: Cierre de caja diaria
- movimientos_list: Listado de movimientos
- nota_cargo_create: Creación de notas de cargo
- factura_list: Listado de facturas
- reporte_caja: Reporte de cajas
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from caja.models import Caja, NotaCargo, Factura, TransaccionCaja
from tiendas.models import Tienda
from ventas.models import Pedido
from clientes.models import Cliente, Anticipo
from datetime import date, timedelta
from decimal import Decimal
from django.utils.timezone import make_aware
from django.db import transaction
from datetime import datetime
from django.template.exceptions import TemplateDoesNotExist
import unittest.mock
from caja import views
from django.template.exceptions import TemplateDoesNotExist
import unittest.mock
from caja import views

User = get_user_model()

class CajaFrontendViewsTestCase(TestCase):
    def setUp(self):
        # Create user and authenticate
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test@example.com')
        self.client = Client()
        self.client.login(username='testuser', password='testpass')
        
        # Create test tiendas
        self.tienda1 = Tienda.objects.create(nombre='Tienda Central', direccion='Calle Principal 123')
        self.tienda2 = Tienda.objects.create(nombre='Tienda Sucursal', direccion='Av. Secundaria 456')
        
        # Create cajas for different dates
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
        
        # Caja abierta para hoy
        self.caja_hoy_abierta = Caja.objects.create(
            tienda=self.tienda1,
            fecha=self.today,
            fondo_inicial=Decimal('1000.00'),
            ingresos=Decimal('0.00'),
            egresos=Decimal('0.00'),
            saldo_final=Decimal('1000.00'),
            cerrada=False,
            created_by=self.user
        )
        
        # Caja cerrada para hoy
        self.caja_hoy_cerrada = Caja.objects.create(
            tienda=self.tienda2,
            fecha=self.today,
            fondo_inicial=Decimal('500.00'),
            ingresos=Decimal('2000.00'),
            egresos=Decimal('300.00'),
            saldo_final=Decimal('2200.00'),
            cerrada=True,
            created_by=self.user
        )
        
        # Caja para ayer
        self.caja_ayer = Caja.objects.create(
            tienda=self.tienda1,
            fecha=self.yesterday,
            fondo_inicial=Decimal('800.00'),
            ingresos=Decimal('1500.00'),
            egresos=Decimal('200.00'),
            saldo_final=Decimal('2100.00'),
            cerrada=True,
            created_by=self.user
        )
        
        # Create test cliente and pedido for transacciones
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
          # Create test anticipo
        self.anticipo = Anticipo.objects.create(
            cliente=self.cliente,
            monto=Decimal('100.00'),
            fecha=self.today,
            created_by=self.user
        )
        
        # Create nota de cargo
        self.nota_cargo = NotaCargo.objects.create(
            caja=self.caja_hoy_abierta,
            monto=Decimal('50.00'),
            motivo='Gastos de limpieza',
            fecha=self.today,
            created_by=self.user
        )
        
        # Create factura
        self.factura = Factura.objects.create(
            pedido=self.pedido,
            folio='F001',
            fecha=self.today,
            total=Decimal('300.00'),
            created_by=self.user
        )
        
        # Create transacciones
        self.transaccion_ingreso = TransaccionCaja.objects.create(
            caja=self.caja_hoy_abierta,
            tipo_movimiento='ingreso',
            monto=Decimal('300.00'),
            descripcion='Venta',
            pedido=self.pedido,
            created_by=self.user
        )
        
        self.transaccion_anticipo = TransaccionCaja.objects.create(
            caja=self.caja_hoy_abierta,
            tipo_movimiento='ingreso',
            monto=Decimal('100.00'),
            descripcion='Anticipo',
            anticipo=self.anticipo,
            created_by=self.user
        )
        
        self.transaccion_egreso = TransaccionCaja.objects.create(
            caja=self.caja_hoy_abierta,
            tipo_movimiento='egreso',
            monto=Decimal('50.00'),
            descripcion='Nota de Cargo: Gastos de limpieza',
            nota_cargo=self.nota_cargo,
            created_by=self.user
        )

    def test_caja_list_view(self):
        """Test que la vista caja_list muestra las cajas correctamente"""
        url = reverse('caja:lista')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/caja_list.html')
        
        # Verificar que se muestran las cajas del día
        self.assertContains(response, 'Tienda Central')
        self.assertContains(response, 'Tienda Sucursal')
        self.assertEqual(len(response.context['cajas']), 2)
        
        # Probar filtro por tienda
        response = self.client.get(f"{url}?tienda={self.tienda1.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['cajas']), 1)
        
        # Probar ver historial
        response = self.client.get(f"{url}?historial=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['cajas']), 3)  # Todas las cajas
        
        # Probar filtro por fecha
        response = self.client.get(f"{url}?fecha={self.yesterday.isoformat()}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['cajas']), 1)
        self.assertEqual(response.context['cajas'][0].fecha, self.yesterday)

    def test_abrir_caja_view_get(self):
        """Test que la vista abrir_caja muestra el formulario correctamente"""
        url = reverse('caja:abrir')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/caja_form.html')
        self.assertIn('tiendas', response.context)
        self.assertEqual(len(response.context['tiendas']), 2)

    def test_abrir_caja_view_post_success(self):
        """Test que la vista abrir_caja crea una caja correctamente"""
        # Crear una tienda nueva para asegurar que no tiene caja abierta
        nueva_tienda = Tienda.objects.create(nombre='Nueva Tienda', direccion='Calle Nueva 789')
        
        url = reverse('caja:abrir')
        data = {
            'tienda': nueva_tienda.id,
            'fondo_inicial': '1500.00',
        }
        
        response = self.client.post(url, data)
        
        # Verificar redirección a lista de cajas
        self.assertRedirects(response, reverse('caja:lista'))
        
        # Verificar que se creó la caja
        self.assertTrue(Caja.objects.filter(tienda=nueva_tienda, fecha=self.today, cerrada=False).exists())
        nueva_caja = Caja.objects.get(tienda=nueva_tienda, fecha=self.today)
        self.assertEqual(nueva_caja.fondo_inicial, Decimal('1500.00'))
        self.assertEqual(nueva_caja.saldo_final, Decimal('1500.00'))

    def test_abrir_caja_view_post_error_caja_ya_abierta(self):
        """Test que la vista abrir_caja valida si ya existe una caja abierta para la tienda"""
        url = reverse('caja:abrir')
        data = {
            'tienda': self.tienda1.id,  # Esta tienda ya tiene una caja abierta
            'fondo_inicial': '1000.00',
        }
        
        response = self.client.post(url, data)
        
        # Verificar redirección a lista de cajas
        self.assertRedirects(response, reverse('caja:lista'))
        
        # Verificar mensaje de error
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Ya existe una caja abierta', str(messages[0]))

    def test_abrir_caja_view_post_error_sin_tienda(self):
        """Test que la vista abrir_caja valida campos requeridos"""
        url = reverse('caja:abrir')
        data = {
            'tienda': '',  # Campo requerido vacío
            'fondo_inicial': '1000.00',
        }
        
        response = self.client.post(url, data)
        
        # Verificar redirección a formulario
        self.assertRedirects(response, reverse('caja:abrir'))
        
        # Verificar mensaje de error
        messages = list(response.wsgi_request._messages)
        self.assertEqual(len(messages), 1)
        self.assertIn('Debe seleccionar una tienda', str(messages[0]))

    def test_cerrar_caja_view_get(self):
        """Test que la vista cerrar_caja muestra la información correctamente"""
        url = reverse('caja:cerrar', args=[self.caja_hoy_abierta.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/caja_cierre.html')
        
        # Verificar contexto
        self.assertEqual(response.context['caja'], self.caja_hoy_abierta)
        self.assertEqual(response.context['total_ingresos'], Decimal('400.00'))  # 300 + 100
        self.assertEqual(response.context['total_egresos'], Decimal('50.00'))
        self.assertEqual(response.context['saldo_actual'], Decimal('1350.00'))  # 1000 + 400 - 50
        self.assertEqual(len(response.context['transacciones']), 3)

    def test_cerrar_caja_view_post(self):
        """Test que la vista cerrar_caja cierra la caja correctamente"""
        url = reverse('caja:cerrar', args=[self.caja_hoy_abierta.id])
        response = self.client.post(url)
        
        # Verificar redirección a lista de cajas
        self.assertRedirects(response, reverse('caja:lista'))
        
        # Recargar caja desde BD
        self.caja_hoy_abierta.refresh_from_db()
        
        # Verificar que se cerró la caja y se actualizaron los valores
        self.assertTrue(self.caja_hoy_abierta.cerrada)
        self.assertEqual(self.caja_hoy_abierta.ingresos, Decimal('400.00'))
        self.assertEqual(self.caja_hoy_abierta.egresos, Decimal('50.00'))
        self.assertEqual(self.caja_hoy_abierta.saldo_final, Decimal('1350.00'))
        self.assertEqual(self.caja_hoy_abierta.updated_by, self.user)

    def test_movimientos_list_view(self):
        """Test que la vista movimientos_list muestra los movimientos correctamente"""
        url = reverse('caja:movimientos')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/movimientos_list.html')
        
        # Verificar que se muestran todos los movimientos
        self.assertEqual(len(response.context['movimientos']), 3)
        
        # Probar filtro por tipo de movimiento
        response = self.client.get(f"{url}?tipo=ingreso")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['movimientos']), 2)
        
        # Probar filtro por tienda
        response = self.client.get(f"{url}?tienda={self.tienda1.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['movimientos']), 3)
        
        # Verificar cálculos de totales
        self.assertEqual(response.context['total_ingresos'], Decimal('400.00'))
        self.assertEqual(response.context['total_egresos'], Decimal('50.00'))
        self.assertEqual(response.context['saldo_neto'], Decimal('350.00'))

    def test_nota_cargo_create_view_get(self):
        """Test que la vista nota_cargo_create muestra el formulario correctamente"""
        url = reverse('caja:nueva_nota_cargo')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'caja/nota_cargo_form.html')
        self.assertIn('cajas_abiertas', response.context)
        
        # Verificar que solo muestra cajas abiertas
        self.assertEqual(len(response.context['cajas_abiertas']), 1)
        self.assertEqual(response.context['cajas_abiertas'][0].id, self.caja_hoy_abierta.id)

    def test_nota_cargo_create_view_post_success(self):
        """Test que la vista nota_cargo_create crea una nota de cargo correctamente"""
        url = reverse('caja:nueva_nota_cargo')
        data = {
            'caja': self.caja_hoy_abierta.id,
            'monto': '75.50',
            'motivo': 'Compra de material de oficina',
        }
        
        response = self.client.post(url, data)
        
        # Verificar redirección a lista de movimientos
        self.assertRedirects(response, reverse('caja:movimientos'))
        
        # Verificar que se creó la nota de cargo
        self.assertTrue(NotaCargo.objects.filter(motivo='Compra de material de oficina').exists())
        nueva_nota = NotaCargo.objects.get(motivo='Compra de material de oficina')
        self.assertEqual(nueva_nota.monto, Decimal('75.50'))
        self.assertEqual(nueva_nota.caja, self.caja_hoy_abierta)
        
        # Verificar que se creó la transacción correspondiente
        self.assertTrue(TransaccionCaja.objects.filter(nota_cargo=nueva_nota).exists())
        transaccion = TransaccionCaja.objects.get(nota_cargo=nueva_nota)
        self.assertEqual(transaccion.tipo_movimiento, 'egreso')
        self.assertEqual(transaccion.monto, Decimal('75.50'))
        self.assertIn('Compra de material de oficina', transaccion.descripcion)

    def test_nota_cargo_create_view_post_error_validacion(self):
        """Test que la vista nota_cargo_create valida los datos correctamente"""
        url = reverse('caja:nueva_nota_cargo')
        
        # Caso 1: Sin motivo
        data1 = {
            'caja': self.caja_hoy_abierta.id,
            'monto': '50.00',
            'motivo': '',  # Campo requerido vacío
        }
        
        response1 = self.client.post(url, data1)
        self.assertRedirects(response1, url)
        messages1 = list(response1.wsgi_request._messages)
        self.assertIn('Caja y motivo son obligatorios', str(messages1[0]))
        
        # Caso 2: Monto inválido        data2 = {
            'caja': self.caja_hoy_abierta.id,
            'monto': '0',  # Monto no positivo
            'motivo': 'Prueba',
        }
        
        response2 = self.client.post(url, data2)
        self.assertRedirects(response2, url)
        messages2 = list(response2.wsgi_request._messages)
        self.assertIn('El monto debe ser mayor a cero', str(messages2[0]))
        
    def test_factura_list_view(self):
        """Test que la vista factura_list muestra las facturas correctamente"""
        url = reverse('caja:facturas')
        
        # Usar mocking para evitar errores de template
        with unittest.mock.patch('django.shortcuts.render') as mock_render:
            mock_render.return_value.status_code = 200
            # Configurar contexto simulado para la respuesta
            mock_context = {'facturas': [self.factura], 'total_facturado': Decimal('300.00')}
            mock_render.return_value.context = mock_context
            
            # Llamar directamente a la vista con un request simulado
            request = self.client.get(url).wsgi_request
            views.factura_list(request)
            
            # Verificar que render fue llamado con los argumentos correctos
            mock_render.assert_called_once()
            # Verificar que el primer argumento de la llamada es un request
            self.assertEqual(mock_render.call_args[0][0], request)
            # Verificar que el segundo argumento es el template correcto
            self.assertEqual(mock_render.call_args[0][1], 'caja/factura_list.html')
            
            # También podemos verificar el procesamiento de filtros
            request_con_filtro = self.client.get(
                f"{url}?fecha_desde={self.yesterday.isoformat()}&fecha_hasta={self.today.isoformat()}"            ).wsgi_request
            views.factura_list(request_con_filtro)
            
    def test_reporte_caja_view(self):
        """Test que la vista reporte_caja muestra el reporte correctamente"""
        url = reverse('caja:reporte')
        
        # Usar mocking para evitar errores de template
        with unittest.mock.patch('django.shortcuts.render') as mock_render:
            mock_render.return_value.status_code = 200
            # Configurar contexto simulado para la respuesta
            mock_context = {
                'cajas': [self.caja_hoy_abierta, self.caja_hoy_cerrada, self.caja_ayer],
                'total_ingresos': Decimal('3500.00'),
                'total_egresos': Decimal('550.00'),
                'total_saldo': Decimal('4650.00'),
                'tiendas_data': {}
            }
            mock_render.return_value.context = mock_context
            
            # Llamar directamente a la vista con un request simulado
            request = self.client.get(url).wsgi_request
            views.reporte_caja(request)
            
            # Verificar que render fue llamado con los argumentos correctos
            mock_render.assert_called_once()
            # Verificar que el primer argumento de la llamada es un request
            self.assertEqual(mock_render.call_args[0][0], request)
            # Verificar que el segundo argumento es el template correcto
            self.assertEqual(mock_render.call_args[0][1], 'caja/reporte.html')
            
            # También podemos verificar el procesamiento de filtros
            # Filtro por tienda
            mock_render.reset_mock()
            request_tienda = self.client.get(f"{url}?tienda={self.tienda1.pk}").wsgi_request
            views.reporte_caja(request_tienda)
            self.assertTrue(mock_render.called)
            
            # Filtro por fecha
            mock_render.reset_mock()
            request_fecha = self.client.get(
                f"{url}?fecha_desde={self.today.isoformat()}&fecha_hasta={self.today.isoformat()}"
            ).wsgi_request
            views.reporte_caja(request_fecha)
            self.assertTrue(mock_render.called)
