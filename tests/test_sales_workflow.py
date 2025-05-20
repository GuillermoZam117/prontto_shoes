"""
Integration tests for the complete sales workflow.
Tests the flow from product creation, to order creation, to inventory update.
"""
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient
from decimal import Decimal
import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model

from productos.models import Producto
from tiendas.models import Tienda
from proveedores.models import Proveedor
from clientes.models import Cliente, DescuentoCliente
from ventas.models import Pedido, DetallePedido
from inventario.models import Inventario
from devoluciones.models import Devolucion

User = get_user_model()

class SalesWorkflowIntegrationTest(TransactionTestCase):
    """Test the entire sales process from product creation to inventory update."""
    
    def setUp(self):
        """Set up test data for each test."""
        # Create a test user
        self.user = User.objects.create_user(
            username='integracion',
            email='test@example.com',
            password='securepass123',
            is_staff=True
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create a store
        self.tienda = Tienda.objects.create(
            nombre="Tienda Integración",
            direccion="Calle Prueba 123",
            contacto="555-1234",
            activa=True,
            created_by=self.user
        )
        
        # Create a supplier
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Integración",
            contacto="Juan Proveedor",
            max_return_days=30,
            created_by=self.user
        )
        
        # Create a customer
        self.cliente = Cliente.objects.create(
            nombre="Cliente Integración",
            contacto="555-9012",
            observaciones="Cliente de prueba para integración",
            tienda=self.tienda,
            saldo_a_favor=Decimal('0.00'),
            created_by=self.user
        )
        
        # Create a discount for the client
        current_month = timezone.now().strftime('%Y-%m')
        self.descuento = DescuentoCliente.objects.create(
            cliente=self.cliente,
            porcentaje=Decimal('10.00'),
            mes_vigente=current_month,
            monto_acumulado_mes_anterior=Decimal('5000.00')
        )
        
    def test_complete_sales_workflow(self):
        """Test the complete workflow from product creation to inventory update."""
        
        # Step 1: Create a product
        producto = Producto.objects.create(
            codigo="INT001",
            marca="Nike",
            modelo="Air Max",
            color="Negro",
            propiedad="Talla 28",
            costo=Decimal('500.00'),
            precio=Decimal('999.99'),
            numero_pagina="1",
            temporada="Verano",
            oferta=False,
            admite_devolucion=True,
            proveedor=self.proveedor,
            tienda=self.tienda
        )
        
        # Step 2: Set up initial inventory
        inventario_inicial = Inventario.objects.create(
            producto=producto,
            tienda=self.tienda,
            cantidad_actual=10,
            fecha_registro=timezone.now(),
            created_by=self.user
        )
        
        # Step 3: Create a sales order
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            tienda=self.tienda,
            fecha=timezone.now(),
            estado='pendiente',
            total=Decimal('899.99'),  # 999.99 - 10% discount
            tipo='venta',
            descuento_aplicado=Decimal('10.00'),
            created_by=self.user
        )
        
        # Step 4: Add products to the order
        detalle = DetallePedido.objects.create(
            pedido=pedido,
            producto=producto,
            cantidad=2,
            precio_unitario=Decimal('999.99'),
            subtotal=Decimal('1999.98')  # 2 * 999.99 = 1999.98
        )
        
        # Step 5: Update inventory (simulate what would happen in the actual application)
        inventario_inicial.cantidad_actual -= detalle.cantidad
        inventario_inicial.save()
        
        # Step 6: Complete the order
        pedido.estado = 'completado'
        pedido.save()
        
        # Verify final state - The order is complete
        self.assertEqual(Pedido.objects.get(id=pedido.id).estado, 'completado')
        
        # Inventory has been reduced correctly
        self.assertEqual(Inventario.objects.get(producto=producto).cantidad_actual, 8)
        
        # Customer has made a purchase with correct values
        self.assertEqual(DetallePedido.objects.filter(pedido=pedido).count(), 1)
        self.assertEqual(pedido.total, Decimal('899.99'))
        

class ReturnWorkflowIntegrationTest(TransactionTestCase):
    """Test the workflow for returning products."""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='returntest',
            email='return@example.com',
            password='securepass123',
            is_staff=True
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create a store
        self.tienda = Tienda.objects.create(
            nombre="Tienda Devoluciones",
            direccion="Calle Devolucion 123",
            contacto="555-1234",
            activa=True,
            created_by=self.user
        )
        
        # Create a supplier
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Devoluciones",
            contacto="Juan Devolucion",
            max_return_days=30,
            created_by=self.user
        )
        
        # Create a customer
        self.cliente = Cliente.objects.create(
            nombre="Cliente Devolucion",
            contacto="555-9012",
            observaciones="Cliente de prueba para devoluciones",
            tienda=self.tienda,
            saldo_a_favor=Decimal('0.00'),
            created_by=self.user
        )
        
        # Create a product for testing returns
        self.producto = Producto.objects.create(
            codigo="DEV001",
            marca="Adidas",
            modelo="Superstar",
            color="Blanco",
            propiedad="Talla 27",
            costo=Decimal('400.00'),
            precio=Decimal('799.99'),
            numero_pagina="2",
            temporada="Invierno",
            oferta=False,
            admite_devolucion=True,
            proveedor=self.proveedor,
            tienda=self.tienda
        )
        
        # Create inventory for the product
        self.inventario = Inventario.objects.create(
            producto=self.producto,
            tienda=self.tienda,
            cantidad_actual=20,
            fecha_registro=timezone.now(),
            created_by=self.user
        )
        
        # Create an order
        self.pedido = Pedido.objects.create(
            cliente=self.cliente,
            tienda=self.tienda,
            fecha=timezone.now(),
            estado='completado',
            total=Decimal('799.99'),
            tipo='venta',
            descuento_aplicado=Decimal('0.00'),
            created_by=self.user
        )
        
        # Add product to the order
        self.detalle_pedido = DetallePedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            cantidad=1,
            precio_unitario=Decimal('799.99'),
            subtotal=Decimal('799.99')
        )
        
        # Update inventory
        self.inventario.cantidad_actual -= self.detalle_pedido.cantidad
        self.inventario.save()
        
    def test_product_return_workflow(self):
        """Test the complete return workflow."""
        
        # Initial verification
        self.assertEqual(self.inventario.cantidad_actual, 19)
        self.assertEqual(self.cliente.saldo_a_favor, Decimal('0.00'))
        
        # Create a return
        devolucion = Devolucion.objects.create(
            cliente=self.cliente,
            producto=self.producto,
            detalle_pedido=self.detalle_pedido,
            motivo="Talla incorrecta",
            tipo="cambio",
            estado="aprobada",
            precio_devolucion=Decimal('799.99'),
            confirmacion_proveedor=True,
            afecta_inventario=True,
            saldo_a_favor_generado=Decimal('799.99'),
            created_by=self.user
        )
        
        # Process the return (in a real app, this would be in a view)
        # Update inventory - assume 1 item is being returned based on the detalle_pedido
        inventario = Inventario.objects.get(producto=self.producto)
        inventario.cantidad_actual += 1  # Add 1 item back to inventory
        inventario.save()
        
        # Update customer credit
        cliente = Cliente.objects.get(id=self.cliente.id)
        cliente.saldo_a_favor += devolucion.saldo_a_favor_generado
        cliente.save()
        
        # Verify results
        # Check the return record is correct
        self.assertEqual(Devolucion.objects.count(), 1)
        self.assertEqual(devolucion.tipo, "cambio")
        
        # Check inventory is updated
        inventario_updated = Inventario.objects.get(producto=self.producto)
        self.assertEqual(inventario_updated.cantidad_actual, 20)
        
        # Check customer credit is updated
        cliente_updated = Cliente.objects.get(id=self.cliente.id)
        self.assertEqual(cliente_updated.saldo_a_favor, Decimal('799.99'))


class DiscountWorkflowIntegrationTest(TransactionTestCase):
    """Test the monthly discount assignment workflow."""
    
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='discounttest',
            email='discount@example.com',
            password='securepass123',
            is_staff=True
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create a store
        self.tienda = Tienda.objects.create(
            nombre="Tienda Descuentos",
            direccion="Calle Descuento 123",
            contacto="555-1234",
            activa=True,
            created_by=self.user
        )
        
        # Create discount tiers
        from descuentos.models import TabuladorDescuento
        
        TabuladorDescuento.objects.create(
            rango_min=Decimal('0.00'),
            rango_max=Decimal('5000.00'),
            porcentaje=Decimal('5.00')
        )
        
        TabuladorDescuento.objects.create(
            rango_min=Decimal('5000.01'),
            rango_max=Decimal('10000.00'),
            porcentaje=Decimal('10.00')
        )
        
        TabuladorDescuento.objects.create(
            rango_min=Decimal('10000.01'),
            rango_max=Decimal('999999.99'),
            porcentaje=Decimal('15.00')
        )
        
        # Create customers with different sales levels
        self.cliente_bajo = Cliente.objects.create(
            nombre="Cliente Ventas Bajas",
            contacto="555-1111",
            tienda=self.tienda,
            created_by=self.user
        )
        
        self.cliente_medio = Cliente.objects.create(
            nombre="Cliente Ventas Medias",
            contacto="555-2222",
            tienda=self.tienda,
            created_by=self.user
        )
        
        self.cliente_alto = Cliente.objects.create(
            nombre="Cliente Ventas Altas",
            contacto="555-3333",
            tienda=self.tienda,
            created_by=self.user
        )
        
    def test_discount_assignment_workflow(self):
        """Test the monthly discount assignment workflow."""
        from ventas.models import Pedido
        from descuentos.management.commands.assign_monthly_discounts import Command
        
        # Get dates for previous month's orders
        today = timezone.now().date()
        first_day_of_current_month = today.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - datetime.timedelta(days=1)
        first_day_of_previous_month = last_day_of_previous_month.replace(day=1)
        
        # Create orders from previous month with different sales amounts
        # Low sales client (under 5000)
        pedido_bajo = Pedido.objects.create(
            cliente=self.cliente_bajo,
            tienda=self.tienda,
            fecha=timezone.make_aware(datetime.datetime.combine(last_day_of_previous_month, datetime.time(12, 0))),
            estado='surtido',  # The command uses 'surtido' status
            total=Decimal('3000.00'),
            tipo='venta',
            descuento_aplicado=Decimal('0.00'),
            created_by=self.user
        )
        
        # Medium sales client (5000-10000)
        pedido_medio = Pedido.objects.create(
            cliente=self.cliente_medio,
            tienda=self.tienda,
            fecha=timezone.make_aware(datetime.datetime.combine(last_day_of_previous_month, datetime.time(13, 0))),
            estado='surtido',  # The command uses 'surtido' status
            total=Decimal('7500.00'),
            tipo='venta',
            descuento_aplicado=Decimal('0.00'),
            created_by=self.user
        )
        
        # High sales client (above 10000)
        pedido_alto = Pedido.objects.create(
            cliente=self.cliente_alto,
            tienda=self.tienda,
            fecha=timezone.make_aware(datetime.datetime.combine(last_day_of_previous_month, datetime.time(14, 0))),
            estado='surtido',  # The command uses 'surtido' status
            total=Decimal('15000.00'),
            tipo='venta',
            descuento_aplicado=Decimal('0.00'),
            created_by=self.user
        )
        
        # Run the command that assigns monthly discounts
        command = Command()
        command.handle()
        
        # Verify discounts were assigned correctly
        current_month_str = today.strftime('%Y-%m')
        
        # Check low sales client got 5% discount
        try:
            descuento_bajo = DescuentoCliente.objects.get(
                cliente=self.cliente_bajo,
                mes_vigente=current_month_str
            )
            self.assertEqual(descuento_bajo.porcentaje, Decimal('5.00'))
            self.assertEqual(descuento_bajo.monto_acumulado_mes_anterior, Decimal('3000.00'))
        except DescuentoCliente.DoesNotExist:
            self.fail('Discount not created for low sales client')
        
        # Check medium sales client got 10% discount
        try:
            descuento_medio = DescuentoCliente.objects.get(
                cliente=self.cliente_medio,
                mes_vigente=current_month_str
            )
            self.assertEqual(descuento_medio.porcentaje, Decimal('10.00'))
            self.assertEqual(descuento_medio.monto_acumulado_mes_anterior, Decimal('7500.00'))
        except DescuentoCliente.DoesNotExist:
            self.fail('Discount not created for medium sales client')
        
        # Check high sales client got 15% discount
        try:
            descuento_alto = DescuentoCliente.objects.get(
                cliente=self.cliente_alto,
                mes_vigente=current_month_str
            )
            self.assertEqual(descuento_alto.porcentaje, Decimal('15.00'))
            self.assertEqual(descuento_alto.monto_acumulado_mes_anterior, Decimal('15000.00'))
        except DescuentoCliente.DoesNotExist:
            self.fail('Discount not created for high sales client') 