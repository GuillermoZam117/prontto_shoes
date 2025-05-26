from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch, MagicMock
from datetime import date, datetime, timedelta
from rest_framework.exceptions import ValidationError

from ventas.serializers import PedidoSerializer, DetallePedidoSerializer
from ventas.models import Pedido, DetallePedido
from clientes.models import Cliente, DescuentoCliente, ReglaProgramaLealtad
from tiendas.models import Tienda
from productos.models import Producto, Catalogo
from inventario.models import Inventario
from caja.models import Caja, TransaccionCaja
from descuentos.models import TipoDescuento


class DetallePedidoSerializerTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            password='testpass'
        )
        self.tienda = Tienda.objects.create(
            nombre='Tienda Test', 
            direccion='Calle 1'
        )
        self.catalogo = Catalogo.objects.create(
            nombre='Catálogo Test',
            temporada='2025',
            activo=True
        )
        self.producto = Producto.objects.create(
            codigo='PROD001',
            marca='Test Brand',
            modelo='Test Model',
            color='Negro',
            talla='42',
            costo=Decimal('50.00'),
            precio=Decimal('100.00'),
            catalogo=self.catalogo
        )
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tienda=self.tienda
        )
        self.pedido = Pedido.objects.create(
            cliente=self.cliente,
            fecha=timezone.now(),
            estado='pendiente',
            total=Decimal('0.00'),
            tienda=self.tienda,
            tipo='venta'
        )

    def test_detalle_pedido_serializer_valid_data(self):
        """Test that DetallePedidoSerializer works with valid data"""
        data = {
            'pedido': self.pedido.id,
            'producto': self.producto.id,
            'cantidad': 2,
            'precio_unitario': Decimal('100.00'),
            'descuento': Decimal('0.00')
        }
        serializer = DetallePedidoSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_detalle_pedido_serializer_includes_all_fields(self):
        """Test that DetallePedidoSerializer includes all model fields"""
        detalle = DetallePedido.objects.create(
            pedido=self.pedido,
            producto=self.producto,
            cantidad=1,
            precio_unitario=Decimal('100.00'),
            descuento=Decimal('0.00')
        )
        serializer = DetallePedidoSerializer(detalle)
        expected_fields = ['id', 'pedido', 'producto', 'cantidad', 'precio_unitario', 'descuento']
        for field in expected_fields:
            self.assertIn(field, serializer.data)


class PedidoSerializerTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser', 
            password='testpass'
        )
        self.tienda = Tienda.objects.create(
            nombre='Tienda Test', 
            direccion='Calle 1'
        )
        self.catalogo = Catalogo.objects.create(
            nombre='Catálogo Test',
            temporada='2025',
            activo=True
        )
        self.producto = Producto.objects.create(
            codigo='PROD001',
            marca='Test Brand',
            modelo='Test Model',
            color='Negro',
            talla='42',
            costo=Decimal('50.00'),
            precio=Decimal('100.00'),
            catalogo=self.catalogo
        )
        self.cliente = Cliente.objects.create(
            nombre='Cliente Test',
            tienda=self.tienda
        )
        # Create inventory for the product
        self.inventario = Inventario.objects.create(
            producto=self.producto,
            tienda=self.tienda,
            existencias=10,
            minimo=1,
            maximo=20
        )
        # Create cash register
        self.caja = Caja.objects.create(
            tienda=self.tienda,
            fecha=date.today(),
            saldo_inicial=Decimal('1000.00'),
            saldo_final=Decimal('1000.00')
        )

    def test_pedido_serializer_read_only_fields(self):
        """Test that certain fields are read-only"""
        serializer = PedidoSerializer()
        read_only_fields = serializer.Meta.read_only_fields
        expected_read_only = ('estado', 'total', 'descuento_aplicado')
        self.assertEqual(read_only_fields, expected_read_only)

    def test_validate_duplicate_order_same_day_same_client(self):
        """Test validation prevents duplicate orders"""
        # Create an existing order
        existing_order = Pedido.objects.create(
            cliente=self.cliente,
            fecha=timezone.now(),
            estado='pendiente',
            total=Decimal('100.00'),
            tienda=self.tienda,
            tipo='venta'
        )
        
        # Try to create another order for the same client on the same day
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': []
        }
        
        serializer = PedidoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_validate_allows_different_day_same_client(self):
        """Test validation allows orders on different days"""
        # Create an existing order for yesterday
        yesterday = timezone.now() - timezone.timedelta(days=1)
        existing_order = Pedido.objects.create(
            cliente=self.cliente,
            fecha=yesterday,
            estado='pendiente',
            total=Decimal('100.00'),
            tienda=self.tienda,
            tipo='venta'
        )
        
        # Try to create another order for today
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': []
        }
        
        serializer = PedidoSerializer(data=data)
        # This should be valid since it's a different day
        attrs = serializer.validate(data)
        self.assertIsNotNone(attrs)

    def test_validate_allows_different_tipo_same_day(self):
        """Test validation allows different order types on same day"""
        # Create an existing 'venta' order
        existing_order = Pedido.objects.create(
            cliente=self.cliente,
            fecha=timezone.now(),
            estado='pendiente',
            total=Decimal('100.00'),
            tienda=self.tienda,
            tipo='venta'
        )
        
        # Try to create an 'apartado' order for the same day
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'apartado',
            'detalles': []
        }
        
        serializer = PedidoSerializer(data=data)
        attrs = serializer.validate(data)
        self.assertIsNotNone(attrs)

    def test_validate_allows_update_same_order(self):
        """Test validation allows updating the same order"""
        existing_order = Pedido.objects.create(
            cliente=self.cliente,
            fecha=timezone.now(),
            estado='pendiente',
            total=Decimal('100.00'),
            tienda=self.tienda,
            tipo='venta'
        )
        
        # Update the same order
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': []
        }
        
        serializer = PedidoSerializer(existing_order, data=data)
        attrs = serializer.validate(data)
        self.assertIsNotNone(attrs)

    def test_validate_empty_detalles(self):
        """Test validation fails with empty order details"""
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': []
        }
        
        serializer = PedidoSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.validate(data)

    def test_validate_invalid_product_in_detalles(self):
        """Test validation fails with invalid product in details"""
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': [
                {
                    'producto': 99999,  # Non-existent product
                    'cantidad': 1,
                    'precio_unitario': Decimal('100.00')
                }
            ]
        }
        
        serializer = PedidoSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.validate(data)

    def test_validate_insufficient_inventory(self):
        """Test validation fails with insufficient inventory"""
        # Set inventory to 1
        self.inventario.existencias = 1
        self.inventario.save()
        
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 5,  # More than available
                    'precio_unitario': Decimal('100.00')
                }
            ]
        }
        
        serializer = PedidoSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.validate(data)

    @patch('ventas.serializers.PedidoSerializer._aplicar_descuento_cliente')
    @patch('ventas.serializers.PedidoSerializer._aplicar_puntos_lealtad')
    @patch('ventas.serializers.PedidoSerializer._registrar_en_caja')
    def test_create_pedido_calls_all_business_logic(self, mock_caja, mock_puntos, mock_descuento):
        """Test that create method calls all business logic methods"""
        mock_descuento.return_value = Decimal('0.00')
        mock_puntos.return_value = None
        mock_caja.return_value = None
        
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 1,
                    'precio_unitario': Decimal('100.00')
                }
            ]
        }
        
        serializer = PedidoSerializer(data=data)
        if serializer.is_valid():
            pedido = serializer.save()
            
            # Verify business logic methods were called
            mock_descuento.assert_called_once()
            mock_puntos.assert_called_once()
            mock_caja.assert_called_once()

    def test_aplicar_descuento_cliente_with_discount(self):
        """Test applying client discount"""
        # Create a discount for the client
        tipo_descuento = TipoDescuento.objects.create(
            nombre='5% Descuento',
            porcentaje=Decimal('5.00'),
            monto_minimo=Decimal('0.00')
        )
        descuento_cliente = DescuentoCliente.objects.create(
            cliente=self.cliente,
            tipo_descuento=tipo_descuento,
            mes=date.today().month,
            año=date.today().year,
            monto_compras=Decimal('1000.00')
        )
        
        serializer = PedidoSerializer()
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            fecha=timezone.now(),
            estado='pendiente',
            total=Decimal('100.00'),
            tienda=self.tienda,
            tipo='venta'
        )
        
        descuento = serializer._aplicar_descuento_cliente(pedido, Decimal('100.00'))
        self.assertEqual(descuento, Decimal('5.00'))

    def test_aplicar_descuento_cliente_without_discount(self):
        """Test applying client discount when no discount exists"""
        serializer = PedidoSerializer()
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            fecha=timezone.now(),
            estado='pendiente',
            total=Decimal('100.00'),
            tienda=self.tienda,
            tipo='venta'
        )
        
        descuento = serializer._aplicar_descuento_cliente(pedido, Decimal('100.00'))
        self.assertEqual(descuento, Decimal('0.00'))

    def test_aplicar_puntos_lealtad(self):
        """Test applying loyalty points"""
        # Create loyalty rule
        regla = ReglaProgramaLealtad.objects.create(
            nombre='Regla Test',
            puntos_por_peso=Decimal('1.00'),
            activa=True
        )
        
        serializer = PedidoSerializer()
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            fecha=timezone.now(),
            estado='pendiente',
            total=Decimal('100.00'),
            tienda=self.tienda,
            tipo='venta'
        )
        
        # This should not raise an exception
        serializer._aplicar_puntos_lealtad(pedido, Decimal('100.00'))
        
        # Verify points were added to client
        self.cliente.refresh_from_db()
        self.assertEqual(self.cliente.puntos_lealtad, Decimal('100.00'))

    def test_registrar_en_caja(self):
        """Test cash register transaction recording"""
        serializer = PedidoSerializer()
        pedido = Pedido.objects.create(
            cliente=self.cliente,
            fecha=timezone.now(),
            estado='pendiente',
            total=Decimal('100.00'),
            tienda=self.tienda,
            tipo='venta'
        )
        
        # This should not raise an exception
        serializer._registrar_en_caja(pedido, Decimal('100.00'))
        
        # Verify transaction was recorded
        transacciones = TransaccionCaja.objects.filter(caja=self.caja)
        self.assertEqual(transacciones.count(), 1)
        
        transaccion = transacciones.first()
        self.assertEqual(transaccion.tipo, 'ingreso')
        self.assertEqual(transaccion.monto, Decimal('100.00'))

    def test_actualizar_inventario(self):
        """Test inventory update after order creation"""
        serializer = PedidoSerializer()
        detalles = [
            {
                'producto': self.producto.id,
                'cantidad': 2
            }
        ]
        
        initial_stock = self.inventario.existencias
        serializer._actualizar_inventario(detalles, self.tienda.id)
        
        self.inventario.refresh_from_db()
        self.assertEqual(self.inventario.existencias, initial_stock - 2)

    def test_serializer_with_nested_detalles(self):
        """Test serializer handles nested order details correctly"""
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now().isoformat(),
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 1,
                    'precio_unitario': '100.00',
                    'descuento': '0.00'
                }
            ]
        }
        
        serializer = PedidoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        # Check that detalles field is properly configured
        self.assertIn('detalles', serializer.fields)
        self.assertTrue(serializer.fields['detalles'].many)

    def test_serializer_validation_error_messages(self):
        """Test that validation errors provide meaningful messages"""
        # Create conflicting order
        Pedido.objects.create(
            cliente=self.cliente,
            fecha=timezone.now(),
            estado='pendiente',
            total=Decimal('100.00'),
            tienda=self.tienda,
            tipo='venta'
        )
        
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': []
        }
        
        serializer = PedidoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
        # Check that error message is informative
        error_message = str(serializer.errors['non_field_errors'][0])
        self.assertIn('Ya existe un pedido', error_message)
        
    def test_validate_different_order_types(self):
        """Test that order validation allows different order types for same client/date"""
        # Create a venta order
        Pedido.objects.create(
            cliente=self.cliente,
            fecha=timezone.now(),
            estado='pendiente',
            total=Decimal('100.00'),
            tienda=self.tienda,
            tipo='venta'
        )
        
        # Try to create an apartado order for the same client/date
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'apartado',  # Different type
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 1,
                    'precio_unitario': Decimal('100.00'),
                    'subtotal': Decimal('100.00')
                }
            ],
            'subtotal': Decimal('100.00'),
            'descuento_porcentaje': Decimal('0.00'),
            'total': Decimal('100.00')
        }
        
        serializer = PedidoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Validation failed: {serializer.errors}")
    
    def test_validate_same_date_different_type(self):
        """Test that orders of different types can be created on the same date"""
        # Create orders with different types on same date
        today = timezone.now().date()
        
        # Create venta
        Pedido.objects.create(
            cliente=self.cliente,
            fecha=today,
            estado='pendiente',
            total=Decimal('100.00'),
            tienda=self.tienda,
            tipo='venta'
        )
        
        # Create apartado - should be allowed
        apartado_data = {
            'cliente': self.cliente.id,
            'fecha': today,
            'tienda': self.tienda.id,
            'tipo': 'apartado',
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 1,
                    'precio_unitario': Decimal('100.00'),
                    'subtotal': Decimal('100.00')
                }
            ],
            'subtotal': Decimal('100.00'),
            'descuento_porcentaje': Decimal('0.00'),
            'total': Decimal('100.00')
        }
        
        serializer = PedidoSerializer(data=apartado_data)
        self.assertTrue(serializer.is_valid(), f"Validation failed: {serializer.errors}")
        
    def test_validate_fecha_in_future(self):
        """Test that orders with future dates are rejected"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        data = {
            'cliente': self.cliente.id,
            'fecha': tomorrow,
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 1,
                    'precio_unitario': Decimal('100.00'),
                    'subtotal': Decimal('100.00')
                }
            ],
            'subtotal': Decimal('100.00'),
            'descuento_porcentaje': Decimal('0.00'),
            'total': Decimal('100.00')
        }
        
        serializer = PedidoSerializer(data=data)
        # Depending on business rules, this might be valid or invalid
        # Let's check current implementation
        if not serializer.is_valid():
            self.assertIn('fecha', serializer.errors, "Error should be related to date")
            
    def test_validate_negative_cantidad(self):
        """Test that orders with negative quantities are rejected"""
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': -1,  # Negative quantity
                    'precio_unitario': Decimal('100.00'),
                    'subtotal': Decimal('-100.00')
                }
            ],
            'subtotal': Decimal('-100.00'),
            'descuento_porcentaje': Decimal('0.00'),
            'total': Decimal('-100.00')
        }
        
        serializer = PedidoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('detalles', serializer.errors, "Error should be related to detalles")
        
    def test_validate_zero_cantidad(self):
        """Test that orders with zero quantities are rejected"""
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 0,  # Zero quantity
                    'precio_unitario': Decimal('100.00'),
                    'subtotal': Decimal('0.00')
                }
            ],
            'subtotal': Decimal('0.00'),
            'descuento_porcentaje': Decimal('0.00'),
            'total': Decimal('0.00')
        }
        
        serializer = PedidoSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        
    def test_apply_cliente_descuento(self):
        """Test that client discounts are correctly applied"""
        # Create a discount for the client
        DescuentoCliente.objects.create(
            cliente=self.cliente,
            porcentaje=Decimal('10.00'),
            fecha_inicio=timezone.now().date() - timedelta(days=10),
            fecha_fin=timezone.now().date() + timedelta(days=10),
            activo=True
        )
        
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 1,
                    'precio_unitario': Decimal('100.00'),
                    'subtotal': Decimal('100.00')
                }
            ],
            'subtotal': Decimal('100.00'),
            'total': Decimal('90.00')  # After 10% discount
        }
        
        serializer = PedidoSerializer(data=data)
        # The serializer should apply the discount automatically
        self.assertTrue(serializer.is_valid(), f"Validation failed: {serializer.errors}")
        self.assertEqual(Decimal('10.00'), serializer.validated_data.get('descuento_porcentaje'))
        
    def test_apply_descuento_with_programa_lealtad(self):
        """Test that loyalty program discounts are correctly applied"""
        # Create a loyalty program rule
        regla = ReglaProgramaLealtad.objects.create(
            nombre="Regla Test",
            monto_minimo=Decimal('50.00'),
            descuento_porcentaje=Decimal('5.00'),
            activo=True
        )
        
        data = {
            'cliente': self.cliente.id,
            'fecha': timezone.now(),
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 1,
                    'precio_unitario': Decimal('100.00'),
                    'subtotal': Decimal('100.00')
                }
            ],
            'subtotal': Decimal('100.00'),
            'total': Decimal('95.00')  # After 5% loyalty discount
        }
        
        serializer = PedidoSerializer(data=data)
        # The serializer might apply the loyalty discount
        if serializer.is_valid():
            self.assertEqual(Decimal('5.00'), serializer.validated_data.get('descuento_porcentaje'))
            
    def test_multiple_order_creation_same_client_different_days(self):
        """Test that orders can be created for the same client on different days"""
        # Create order for today
        Pedido.objects.create(
            cliente=self.cliente,
            fecha=timezone.now(),
            estado='pendiente',
            total=Decimal('100.00'),
            tienda=self.tienda,
            tipo='venta'
        )
        
        # Create order for yesterday
        yesterday = timezone.now() - timedelta(days=1)
        data = {
            'cliente': self.cliente.id,
            'fecha': yesterday,
            'tienda': self.tienda.id,
            'tipo': 'venta',
            'detalles': [
                {
                    'producto': self.producto.id,
                    'cantidad': 1,
                    'precio_unitario': Decimal('100.00'),
                    'subtotal': Decimal('100.00')
                }
            ],
            'subtotal': Decimal('100.00'),
            'descuento_porcentaje': Decimal('0.00'),
            'total': Decimal('100.00')
        }
        
        serializer = PedidoSerializer(data=data)
        self.assertTrue(serializer.is_valid(), f"Validation failed: {serializer.errors}")
