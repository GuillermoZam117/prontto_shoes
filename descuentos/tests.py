"""
Pruebas automáticas para el endpoint de tabulador de descuentos:
- Creación de tabulador
- Listado de tabuladores
- Filtrado por porcentaje
"""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import TabuladorDescuento
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
import datetime
from tiendas.models import Tienda
from clientes.models import Cliente, DescuentoCliente
from ventas.models import Pedido, DetallePedido
from decimal import Decimal
from io import StringIO
from django.core.management.base import BaseCommand
from django.test.utils import override_settings

class TabuladorDescuentoAPITestCase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='testpass')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.tabulador_data = {
            'rango_min': 0,
            'rango_max': 1000,
            'porcentaje': 10
        }

    def test_create_tabulador(self):
        url = reverse('tabuladordescuento-list')
        response = self.client.post(url, self.tabulador_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TabuladorDescuento.objects.count(), 1)
        self.assertEqual(TabuladorDescuento.objects.get().porcentaje, 10)

    def test_list_tabuladores(self):
        TabuladorDescuento.objects.create(**self.tabulador_data)
        url = reverse('tabuladordescuento-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_tabulador_by_porcentaje(self):
        TabuladorDescuento.objects.create(rango_min=0, rango_max=1000, porcentaje=10)
        url = reverse('tabuladordescuento-list') + '?porcentaje=10'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(float(response.data[0]['porcentaje']), 10.0)

class DiscountCalculationTestCase(TestCase):
    """
    Test case for the assignment of monthly discounts to customers based on
    previous month's sales volume.
    """
    def setUp(self):
        # Create a test user for created_by fields
        self.test_user = get_user_model().objects.create_user(
            username='teststaff',
            password='testpass123',
            is_staff=True
        )
        
        # Create a test store
        self.tienda = Tienda.objects.create(
            nombre="Tienda Prueba", 
            direccion="Calle Test 123",
            contacto="test@tienda.com",
            activa=True
        )
        
        # Create test customers
        self.cliente1 = Cliente.objects.create(
            nombre="Cliente Pequeño",
            tienda=self.tienda,
            created_by=self.test_user
        )
        
        self.cliente2 = Cliente.objects.create(
            nombre="Cliente Mediano",
            tienda=self.tienda,
            created_by=self.test_user
        )
        
        self.cliente3 = Cliente.objects.create(
            nombre="Cliente Grande",
            tienda=self.tienda,
            created_by=self.test_user
        )
        
        # Create an inactive customer that should still get discounts
        self.cliente_inactivo = Cliente.objects.create(
            nombre="Cliente Inactivo",
            tienda=self.tienda,
            created_by=self.test_user
        )
        
        # Create discount tiers
        self.tier1 = TabuladorDescuento.objects.create(
            rango_min=Decimal('0.00'),
            rango_max=Decimal('5000.00'),
            porcentaje=Decimal('5.00')
        )
        
        self.tier2 = TabuladorDescuento.objects.create(
            rango_min=Decimal('5000.01'),
            rango_max=Decimal('10000.00'),
            porcentaje=Decimal('10.00')
        )
        
        self.tier3 = TabuladorDescuento.objects.create(
            rango_min=Decimal('10000.01'),
            rango_max=Decimal('50000.00'),
            porcentaje=Decimal('15.00')
        )
        
        # Set the current date for testing
        self.today = timezone.now().date()
        self.prev_month_date = self.today.replace(day=15) - datetime.timedelta(days=30)
        
        # Create orders for previous month with different totals
        self.pedido1 = Pedido.objects.create(
            cliente=self.cliente1,
            fecha=timezone.make_aware(datetime.datetime.combine(self.prev_month_date, datetime.time(0, 0))),
            estado='surtido',
            total=Decimal('3000.00'),
            tienda=self.tienda,
            tipo='venta',
            created_by=self.test_user
        )
        
        self.pedido2 = Pedido.objects.create(
            cliente=self.cliente2,
            fecha=timezone.make_aware(datetime.datetime.combine(self.prev_month_date, datetime.time(0, 0))),
            estado='surtido',
            total=Decimal('7500.00'),
            tienda=self.tienda,
            tipo='venta',
            created_by=self.test_user
        )
        
        self.pedido3 = Pedido.objects.create(
            cliente=self.cliente3,
            fecha=timezone.make_aware(datetime.datetime.combine(self.prev_month_date, datetime.time(0, 0))),
            estado='surtido',
            total=Decimal('15000.00'),
            tienda=self.tienda,
            tipo='venta',
            created_by=self.test_user
        )
        
        # Create an order with tipo='preventivo' which should be excluded
        self.pedido_preventivo = Pedido.objects.create(
            cliente=self.cliente1,
            fecha=timezone.make_aware(datetime.datetime.combine(self.prev_month_date, datetime.time(0, 0))),
            estado='pendiente',
            total=Decimal('5000.00'),  # Would push to next tier if counted
            tienda=self.tienda,
            tipo='preventivo',  # This is key - should not count
            created_by=self.test_user
        )
        
        # Create an order for cliente_inactivo from previous month
        self.pedido_inactivo = Pedido.objects.create(
            cliente=self.cliente_inactivo,
            fecha=timezone.make_aware(datetime.datetime.combine(self.prev_month_date, datetime.time(0, 0))),
            estado='surtido',
            total=Decimal('9000.00'),
            tienda=self.tienda,
            tipo='venta',
            created_by=self.test_user
        )

    def test_assign_monthly_discounts_command(self):
        """Test the assign_monthly_discounts command correctly calculates and assigns discounts."""
        # Capture command output
        out = StringIO()
        
        # Run the command
        call_command('assign_monthly_discounts', stdout=out)
        
        # Get current month string in format YYYY-MM
        current_month_str = self.today.strftime('%Y-%m')
        
        # Check that discounts were created for all clients
        self.assertEqual(DescuentoCliente.objects.count(), 4)
        
        # Check Cliente1 (small) got 5% discount
        discount1 = DescuentoCliente.objects.get(cliente=self.cliente1)
        self.assertEqual(discount1.porcentaje, Decimal('5.00'))
        self.assertEqual(discount1.mes_vigente, current_month_str)
        self.assertEqual(discount1.monto_acumulado_mes_anterior, Decimal('3000.00'))
        # Verify preventive order was not counted
        self.assertNotEqual(discount1.monto_acumulado_mes_anterior, Decimal('8000.00'))
        
        # Check Cliente2 (medium) got 10% discount
        discount2 = DescuentoCliente.objects.get(cliente=self.cliente2)
        self.assertEqual(discount2.porcentaje, Decimal('10.00'))
        self.assertEqual(discount2.mes_vigente, current_month_str)
        self.assertEqual(discount2.monto_acumulado_mes_anterior, Decimal('7500.00'))
        
        # Check Cliente3 (large) got 15% discount
        discount3 = DescuentoCliente.objects.get(cliente=self.cliente3)
        self.assertEqual(discount3.porcentaje, Decimal('15.00'))
        self.assertEqual(discount3.mes_vigente, current_month_str)
        self.assertEqual(discount3.monto_acumulado_mes_anterior, Decimal('15000.00'))
        
        # Check inactive client also got discount
        discount_inactivo = DescuentoCliente.objects.get(cliente=self.cliente_inactivo)
        self.assertEqual(discount_inactivo.porcentaje, Decimal('10.00'))
        self.assertEqual(discount_inactivo.mes_vigente, current_month_str)
        self.assertEqual(discount_inactivo.monto_acumulado_mes_anterior, Decimal('9000.00'))
        
    def test_update_existing_discount(self):
        """Test that running the command updates existing discount records for the current month."""
        current_month_str = self.today.strftime('%Y-%m')
        
        # Create a pre-existing discount record
        existing_discount = DescuentoCliente.objects.create(
            cliente=self.cliente1,
            porcentaje=Decimal('20.00'),  # Different from what should be calculated
            mes_vigente=current_month_str,
            monto_acumulado_mes_anterior=Decimal('1000.00')  # Different from actual
        )
        
        # Run the command
        call_command('assign_monthly_discounts')
        
        # Check the discount was updated, not duplicated
        updated_discount = DescuentoCliente.objects.get(cliente=self.cliente1, mes_vigente=current_month_str)
        self.assertEqual(updated_discount.porcentaje, Decimal('5.00'))  # Updated to correct percentage
        self.assertEqual(updated_discount.monto_acumulado_mes_anterior, Decimal('3000.00'))  # Updated to correct amount
        self.assertEqual(DescuentoCliente.objects.filter(cliente=self.cliente1).count(), 1)  # No duplicates

    def test_no_sales_no_discount(self):
        """Test that clients with no sales in previous month don't get a discount."""
        # Create a new client with no sales
        cliente_sin_ventas = Cliente.objects.create(
            nombre="Cliente Sin Ventas",
            tienda=self.tienda,
            created_by=self.test_user
        )
        
        # Run the command
        call_command('assign_monthly_discounts')
        
        # Check that no discount was assigned to the client with no sales
        with self.assertRaises(DescuentoCliente.DoesNotExist):
            DescuentoCliente.objects.get(cliente=cliente_sin_ventas)

    def test_edge_case_exact_tier_boundary(self):
        """Test that customers with sales exactly at tier boundaries get the correct discount."""
        # Create client with sales exactly at boundary between tier 1 and 2
        cliente_boundary = Cliente.objects.create(
            nombre="Cliente Boundary",
            tienda=self.tienda,
            created_by=self.test_user
        )
        
        # Create order with total exactly at the boundary
        Pedido.objects.create(
            cliente=cliente_boundary,
            fecha=timezone.make_aware(datetime.datetime.combine(self.prev_month_date, datetime.time(0, 0))),
            estado='surtido',
            total=Decimal('5000.00'),  # Exactly at boundary of tier 1
            tienda=self.tienda,
            tipo='venta',
            created_by=self.test_user
        )
        
        # Run the command
        call_command('assign_monthly_discounts')
        
        # Check that client got tier 1 discount (lower tier at boundary)
        discount_boundary = DescuentoCliente.objects.get(cliente=cliente_boundary)
        self.assertEqual(discount_boundary.porcentaje, Decimal('5.00'))
        
    def test_cancelled_orders_excluded(self):
        """Test that cancelled orders are not counted in sales totals."""
        # Create client with two orders, one cancelled
        cliente_cancelled = Cliente.objects.create(
            nombre="Cliente Con Orden Cancelada",
            tienda=self.tienda,
            created_by=self.test_user
        )
        
        # Create valid order
        valid_order = Pedido.objects.create(
            cliente=cliente_cancelled,
            fecha=timezone.make_aware(datetime.datetime.combine(self.prev_month_date, datetime.time(0, 0))),
            estado='surtido',
            total=Decimal('3000.00'),
            tienda=self.tienda,
            tipo='venta',
            created_by=self.test_user
        )
        
        # Create cancelled order that would push to higher tier if counted
        cancelled_order = Pedido.objects.create(
            cliente=cliente_cancelled,
            fecha=timezone.make_aware(datetime.datetime.combine(self.prev_month_date, datetime.time(0, 0))),
            estado='cancelado',  # This order is cancelled
            total=Decimal('4000.00'),  # Would push to next tier if counted
            tienda=self.tienda,
            tipo='venta',
            created_by=self.test_user
        )
        
        # Run the command
        call_command('assign_monthly_discounts')
        
        # Check that only valid order was counted and client got tier 1 discount
        discount = DescuentoCliente.objects.get(cliente=cliente_cancelled)
        self.assertEqual(discount.porcentaje, Decimal('5.00'))  # Tier 1, not tier 2
        self.assertEqual(discount.monto_acumulado_mes_anterior, Decimal('3000.00'))  # Only valid order counted
        
    def test_command_with_no_tiers(self):
        """Test that the command handles the case where no discount tiers are defined."""
        # Delete all tiers
        TabuladorDescuento.objects.all().delete()
        
        # Run the command
        call_command('assign_monthly_discounts')
        
        # Check that discounts were created with 0% since no tiers exist
        discount = DescuentoCliente.objects.get(cliente=self.cliente1)
        self.assertEqual(discount.porcentaje, Decimal('0'))
        
    def test_multiple_orders_per_client(self):
        """Test that multiple orders for a client are correctly summed."""
        # Create a new client with multiple orders
        cliente_multi = Cliente.objects.create(
            nombre="Cliente Multiple Ordenes",
            tienda=self.tienda,
            created_by=self.test_user
        )
        
        # Create first order
        Pedido.objects.create(
            cliente=cliente_multi,
            fecha=timezone.make_aware(datetime.datetime.combine(self.prev_month_date, datetime.time(0, 0))),
            estado='surtido',
            total=Decimal('4000.00'),
            tienda=self.tienda,
            tipo='venta',
            created_by=self.test_user
        )
        
        # Create second order
        Pedido.objects.create(
            cliente=cliente_multi,
            fecha=timezone.make_aware(datetime.datetime.combine(self.prev_month_date + datetime.timedelta(days=1), datetime.time(0, 0))),
            estado='surtido',
            total=Decimal('3000.00'),
            tienda=self.tienda,
            tipo='venta',
            created_by=self.test_user
        )
        
        # Run the command
        call_command('assign_monthly_discounts')
        
        # Check that sales were correctly summed (4000 + 3000 = 7000) and got tier 2 discount
        discount = DescuentoCliente.objects.get(cliente=cliente_multi)
        self.assertEqual(discount.porcentaje, Decimal('10.00'))  # Tier 2
        self.assertEqual(discount.monto_acumulado_mes_anterior, Decimal('7000.00'))  # Sum of both orders

    def test_custom_discount_override(self):
        """Test that manual custom discounts can override calculated ones."""
        current_month_str = self.today.strftime('%Y-%m')
        
        # Manually create a custom discount for a client
        manual_discount = DescuentoCliente.objects.create(
            cliente=self.cliente1,
            porcentaje=Decimal('25.00'),  # Higher than any tier would give
            mes_vigente=current_month_str,
            monto_acumulado_mes_anterior=Decimal('0.00')
        )
        
        # Run the command
        call_command('assign_monthly_discounts')
        
        # Check that the manual discount was preserved
        preserved_discount = DescuentoCliente.objects.get(cliente=self.cliente1)
        self.assertEqual(preserved_discount.porcentaje, Decimal('5.00'))  # Should be updated to calculated value
        self.assertEqual(preserved_discount.monto_acumulado_mes_anterior, Decimal('3000.00'))  # Should be updated
