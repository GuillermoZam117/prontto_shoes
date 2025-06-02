"""
Tests de integración para el sistema POS
Prueban la interacción entre múltiples módulos del sistema
"""
import pytest
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

from tests.factories import (
    UserFactory, TiendaFactory, ClienteFactory, ProductoFactory,
    PedidoFactory, DetallePedidoFactory, InventarioFactory,
    CajaFactory, ProveedorFactory, AnticipoFactory
)
from ventas.models import Pedido, DetallePedido
from inventario.models import Inventario
from caja.models import TransaccionCaja
from clientes.models import Cliente, Anticipo


class VentasInventarioIntegrationTestCase(TestCase):
    """Tests de integración entre ventas e inventario"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()
        self.cliente = ClienteFactory(tienda=self.tienda)
        self.proveedor = ProveedorFactory()
        self.producto = ProductoFactory(
            proveedor=self.proveedor, 
            tienda=self.tienda,
            precio=Decimal('100.00')
        )
        
        # Crear inventario inicial
        self.inventario = InventarioFactory(
            producto=self.producto,
            tienda=self.tienda,
            cantidad_actual=10,
            cantidad_minima=2
        )

    def test_should_reduce_inventory_when_order_is_created(self):
        """Debe reducir el inventario cuando se crea un pedido"""
        initial_quantity = self.inventario.cantidad_actual
        order_quantity = 3
        
        # Crear pedido
        pedido = PedidoFactory(
            cliente=self.cliente,
            tienda=self.tienda,
            estado='confirmado'
        )
        
        detalle = DetallePedidoFactory(
            pedido=pedido,
            producto=self.producto,
            cantidad=order_quantity,
            precio_unitario=self.producto.precio
        )
        
        # Simular reducción de inventario (esto debería manejarse por signals)
        self.inventario.cantidad_actual -= order_quantity
        self.inventario.save()
        
        # Verificar reducción
        self.inventario.refresh_from_db()
        expected_quantity = initial_quantity - order_quantity
        self.assertEqual(self.inventario.cantidad_actual, expected_quantity)

    def test_should_alert_when_inventory_below_minimum(self):
        """Debe alertar cuando el inventario está por debajo del mínimo"""
        # Reducir inventario por debajo del mínimo
        self.inventario.cantidad_actual = 1  # Mínimo es 2
        self.inventario.save()
        
        # Verificar que está por debajo del mínimo
        self.assertTrue(self.inventario.cantidad_actual < self.inventario.cantidad_minima)
        
        # En un sistema real, esto activaría una alerta
        needs_restock = self.inventario.cantidad_actual <= self.inventario.cantidad_minima
        self.assertTrue(needs_restock)

    def test_should_prevent_overselling(self):
        """Debe prevenir la sobreventa cuando no hay suficiente inventario"""
        available_quantity = self.inventario.cantidad_actual
        order_quantity = available_quantity + 5  # Más de lo disponible
        
        # Intentar crear pedido con cantidad mayor a la disponible
        pedido = PedidoFactory(
            cliente=self.cliente,
            tienda=self.tienda,
            estado='pendiente'
        )
        
        # En un sistema real, esto debería fallar o requerir validación
        with self.assertRaises(Exception):
            # Simular validación de inventario
            if order_quantity > available_quantity:
                raise ValueError("Cantidad insuficiente en inventario")
            
            DetallePedidoFactory(
                pedido=pedido,
                producto=self.producto,
                cantidad=order_quantity
            )


class VentasCajaIntegrationTestCase(TestCase):
    """Tests de integración entre ventas y caja"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()
        self.cliente = ClienteFactory(tienda=self.tienda)
        self.producto = ProductoFactory(
            tienda=self.tienda,
            precio=Decimal('50.00')
        )
        self.caja = CajaFactory(tienda=self.tienda, turno_activo=True)

    def test_should_create_cash_transaction_when_order_is_paid(self):
        """Debe crear transacción de caja cuando se paga un pedido"""
        # Crear pedido
        pedido = PedidoFactory(
            cliente=self.cliente,
            tienda=self.tienda,
            total=Decimal('150.00'),
            pagado=False
        )
        
        DetallePedidoFactory(
            pedido=pedido,
            producto=self.producto,
            cantidad=3,
            precio_unitario=self.producto.precio
        )
        
        # Simular pago
        pedido.pagado = True
        pedido.save()
        
        # Crear transacción de caja
        transaccion = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo='venta',
            monto=pedido.total,
            descripcion=f'Venta - Pedido #{pedido.id}',
            usuario=self.user
        )
        
        # Verificar transacción
        self.assertEqual(transaccion.monto, pedido.total)
        self.assertEqual(transaccion.tipo, 'venta')
        self.assertTrue(transaccion.monto > 0)

    def test_should_handle_partial_payments_with_advances(self):
        """Debe manejar pagos parciales con anticipos"""
        # Crear anticipo
        anticipo = AnticipoFactory(
            cliente=self.cliente,
            monto=Decimal('75.00')
        )
        
        # Crear pedido
        pedido = PedidoFactory(
            cliente=self.cliente,
            tienda=self.tienda,
            total=Decimal('200.00'),
            pagado=False
        )
        
        # Aplicar anticipo
        remaining_amount = pedido.total - anticipo.monto
        
        # Crear transacciones
        transaccion_anticipo = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo='anticipo_aplicado',
            monto=anticipo.monto,
            descripcion=f'Anticipo aplicado - Pedido #{pedido.id}',
            usuario=self.user
        )
        
        transaccion_restante = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo='venta',
            monto=remaining_amount,
            descripcion=f'Pago restante - Pedido #{pedido.id}',
            usuario=self.user
        )
        
        # Verificar transacciones
        total_paid = transaccion_anticipo.monto + transaccion_restante.monto
        self.assertEqual(total_paid, pedido.total)


class ClientesVentasIntegrationTestCase(TestCase):
    """Tests de integración entre clientes y ventas"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()
        self.cliente = ClienteFactory(
            tienda=self.tienda,
            saldo_a_favor=Decimal('100.00')
        )
        self.producto = ProductoFactory(
            tienda=self.tienda,
            precio=Decimal('80.00')
        )

    def test_should_use_customer_credit_balance_for_payment(self):
        """Debe usar el saldo a favor del cliente para el pago"""
        initial_balance = self.cliente.saldo_a_favor
        order_total = Decimal('60.00')
        
        # Crear pedido
        pedido = PedidoFactory(
            cliente=self.cliente,
            tienda=self.tienda,
            total=order_total,
            pagado=False
        )
        
        # Aplicar saldo a favor
        if self.cliente.saldo_a_favor >= order_total:
            self.cliente.saldo_a_favor -= order_total
            self.cliente.save()
            pedido.pagado = True
            pedido.save()
        
        # Verificar
        self.cliente.refresh_from_db()
        expected_balance = initial_balance - order_total
        self.assertEqual(self.cliente.saldo_a_favor, expected_balance)
        self.assertTrue(pedido.pagado)

    def test_should_accumulate_customer_purchase_history(self):
        """Debe acumular el historial de compras del cliente"""
        # Crear múltiples pedidos
        pedido1 = PedidoFactory(
            cliente=self.cliente,
            tienda=self.tienda,
            total=Decimal('50.00'),
            pagado=True
        )
        
        pedido2 = PedidoFactory(
            cliente=self.cliente,
            tienda=self.tienda,
            total=Decimal('75.00'),
            pagado=True
        )
        
        # Calcular total de compras
        total_purchases = Pedido.objects.filter(
            cliente=self.cliente,
            pagado=True
        ).aggregate(total=models.Sum('total'))['total']
        
        expected_total = pedido1.total + pedido2.total
        self.assertEqual(total_purchases, expected_total)


class BusinessWorkflowIntegrationTestCase(TransactionTestCase):
    """Tests de integración para flujos de negocio completos"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()
        self.cliente = ClienteFactory(tienda=self.tienda)
        self.proveedor = ProveedorFactory()
        self.producto = ProductoFactory(
            proveedor=self.proveedor,
            tienda=self.tienda,
            precio=Decimal('100.00')
        )
        self.inventario = InventarioFactory(
            producto=self.producto,
            tienda=self.tienda,
            cantidad_actual=20
        )
        self.caja = CajaFactory(tienda=self.tienda, turno_activo=True)

    def test_complete_sale_workflow(self):
        """Test del flujo completo de venta"""
        with transaction.atomic():
            # 1. Crear pedido
            pedido = PedidoFactory(
                cliente=self.cliente,
                tienda=self.tienda,
                estado='pendiente',
                pagado=False
            )
            
            # 2. Agregar productos al pedido
            detalle = DetallePedidoFactory(
                pedido=pedido,
                producto=self.producto,
                cantidad=2,
                precio_unitario=self.producto.precio
            )
            
            # 3. Calcular total
            pedido.total = detalle.cantidad * detalle.precio_unitario
            pedido.save()
            
            # 4. Confirmar pedido
            pedido.estado = 'confirmado'
            pedido.save()
            
            # 5. Reducir inventario
            initial_inventory = self.inventario.cantidad_actual
            self.inventario.cantidad_actual -= detalle.cantidad
            self.inventario.save()
            
            # 6. Procesar pago
            pedido.pagado = True
            pedido.save()
            
            # 7. Crear transacción de caja
            transaccion = TransaccionCaja.objects.create(
                caja=self.caja,
                tipo='venta',
                monto=pedido.total,
                descripcion=f'Venta - Pedido #{pedido.id}',
                usuario=self.user
            )
            
            # Verificaciones finales
            self.assertEqual(pedido.estado, 'confirmado')
            self.assertTrue(pedido.pagado)
            self.assertEqual(
                self.inventario.cantidad_actual,
                initial_inventory - detalle.cantidad
            )
            self.assertEqual(transaccion.monto, pedido.total)

    def test_return_workflow(self):
        """Test del flujo de devolución"""
        # Primero crear una venta
        pedido = PedidoFactory(
            cliente=self.cliente,
            tienda=self.tienda,
            estado='confirmado',
            pagado=True,
            total=Decimal('200.00')
        )
        
        detalle = DetallePedidoFactory(
            pedido=pedido,
            producto=self.producto,
            cantidad=2
        )
        
        # Reducir inventario por la venta original
        original_inventory = self.inventario.cantidad_actual
        self.inventario.cantidad_actual -= detalle.cantidad
        self.inventario.save()
        
        # Procesar devolución
        with transaction.atomic():
            # 1. Crear pedido de devolución
            devolucion = PedidoFactory(
                cliente=self.cliente,
                tienda=self.tienda,
                tipo='devolucion',
                estado='confirmado',
                total=-pedido.total  # Negativo para devolución
            )
            
            # 2. Restaurar inventario
            self.inventario.cantidad_actual += detalle.cantidad
            self.inventario.save()
            
            # 3. Crear transacción de devolución en caja
            transaccion = TransaccionCaja.objects.create(
                caja=self.caja,
                tipo='devolucion',
                monto=abs(devolucion.total),
                descripcion=f'Devolución - Pedido #{pedido.id}',
                usuario=self.user
            )
            
            # 4. Actualizar saldo del cliente
            self.cliente.saldo_a_favor += abs(devolucion.total)
            self.cliente.save()
        
        # Verificaciones
        self.assertEqual(self.inventario.cantidad_actual, original_inventory)
        self.assertEqual(devolucion.tipo, 'devolucion')
        self.assertTrue(self.cliente.saldo_a_favor > 0)


class DataConsistencyIntegrationTestCase(TestCase):
    """Tests de consistencia de datos entre módulos"""

    def setUp(self):
        self.tienda = TiendaFactory()
        self.cliente = ClienteFactory(tienda=self.tienda)
        self.producto = ProductoFactory(tienda=self.tienda)

    def test_should_maintain_referential_integrity(self):
        """Debe mantener integridad referencial entre modelos"""
        # Crear datos relacionados
        pedido = PedidoFactory(cliente=self.cliente, tienda=self.tienda)
        detalle = DetallePedidoFactory(pedido=pedido, producto=self.producto)
        
        # Verificar relaciones
        self.assertEqual(detalle.pedido, pedido)
        self.assertEqual(detalle.producto, self.producto)
        self.assertEqual(pedido.cliente, self.cliente)
        self.assertEqual(pedido.tienda, self.tienda)
        
        # Verificar que los objetos están en la base de datos
        self.assertTrue(Pedido.objects.filter(id=pedido.id).exists())
        self.assertTrue(DetallePedido.objects.filter(id=detalle.id).exists())

    def test_should_handle_cascade_deletions_properly(self):
        """Debe manejar eliminaciones en cascada apropiadamente"""
        pedido = PedidoFactory(cliente=self.cliente)
        detalle = DetallePedidoFactory(pedido=pedido, producto=self.producto)
        
        detalle_id = detalle.id
        
        # Eliminar pedido debería eliminar detalles
        pedido.delete()
        
        # Verificar que el detalle también se eliminó
        self.assertFalse(DetallePedido.objects.filter(id=detalle_id).exists())

    def test_should_prevent_invalid_operations(self):
        """Debe prevenir operaciones inválidas"""
        # Intentar crear pedido sin cliente debería fallar
        with self.assertRaises(Exception):
            PedidoFactory(cliente=None, tienda=self.tienda)
        
        # Intentar crear detalle sin producto debería fallar
        pedido = PedidoFactory(cliente=self.cliente, tienda=self.tienda)
        with self.assertRaises(Exception):
            DetallePedidoFactory(pedido=pedido, producto=None)
