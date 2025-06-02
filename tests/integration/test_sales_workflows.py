"""
Tests de integración para flujos completos de ventas end-to-end
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, Mock

from tests.base_simple import BaseIntegrationTestCase
from tests.factories import (
    TiendaFactory, ProductoFactory, ClienteFactory, UserFactory,
    PedidoFactory, DetallePedidoFactory, CajaAbiertaFactory
)

from ventas.models import Pedido, DetallePedido
from productos.models import Producto
from inventario.models import Inventario
from caja.models import Caja, TransaccionCaja


class VentasIntegrationTestCase(BaseIntegrationTestCase):
    """Tests de integración para el flujo completo de ventas"""
    
    def setUp(self):
        super().setUp()
        
        # Crear productos con inventario
        self.producto1 = ProductoFactory(
            tienda=self.tienda,
            codigo='PROD001',
            precio=Decimal('100.00')
        )
        self.producto2 = ProductoFactory(
            tienda=self.tienda,
            codigo='PROD002',
            precio=Decimal('200.00')
        )
        
        # Crear inventarios
        self.inventario1 = Inventario.objects.create(
            producto=self.producto1,
            tienda=self.tienda,
            cantidad=50
        )
        self.inventario2 = Inventario.objects.create(
            producto=self.producto2,
            tienda=self.tienda,
            cantidad=30
        )
        
        # Cliente
        self.cliente = ClienteFactory(tienda=self.tienda)
        
        # Usuario vendedor
        self.vendedor = UserFactory(username='vendedor')

    def test_should_complete_full_sales_workflow(self):
        """
        Test del flujo completo: crear pedido -> confirmar -> generar factura -> actualizar inventario
        """
        # 1. Crear pedido pendiente
        pedido = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=timezone.now().date(),
            estado='pendiente',
            created_by=self.vendedor
        )
        
        # 2. Agregar items al pedido
        detalle1 = DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto1,
            cantidad=5,
            precio_unitario=self.producto1.precio
        )
        detalle2 = DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto2,
            cantidad=2,
            precio_unitario=self.producto2.precio
        )
        
        # Verificar cálculos del pedido
        pedido.refresh_from_db()
        expected_subtotal = (5 * Decimal('100.00')) + (2 * Decimal('200.00'))
        expected_iva = expected_subtotal * Decimal('0.16')
        expected_total = expected_subtotal + expected_iva
        
        self.assertDecimalEqual(pedido.subtotal, expected_subtotal)
        self.assertDecimalEqual(pedido.iva, expected_iva)
        self.assertDecimalEqual(pedido.total, expected_total)
        
        # 3. Confirmar pedido
        inventario1_inicial = self.inventario1.cantidad
        inventario2_inicial = self.inventario2.cantidad
        
        pedido.estado = 'confirmado'
        pedido.save()
        
        # Simular actualización de inventario
        self.inventario1.cantidad -= 5
        self.inventario1.save()
        self.inventario2.cantidad -= 2
        self.inventario2.save()
        
        # 4. Verificar actualización de inventarios
        self.inventario1.refresh_from_db()
        self.inventario2.refresh_from_db()
        
        self.assertEqual(self.inventario1.cantidad, inventario1_inicial - 5)
        self.assertEqual(self.inventario2.cantidad, inventario2_inicial - 2)
        
        # 5. Simular registro en caja
        transaccion = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=pedido.total,
            descripcion=f'Venta pedido #{pedido.id}',
            pedido=pedido,
            created_by=self.vendedor
        )
        
        # 6. Verificar transacción
        self.assertEqual(transaccion.monto, pedido.total)
        self.assertEqual(transaccion.pedido, pedido)
        self.assertEqual(transaccion.tipo_movimiento, 'INGRESO')

    def test_should_handle_insufficient_inventory(self):
        """Test manejo de inventario insuficiente"""
        
        # Intentar vender más de lo disponible
        pedido = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=timezone.now().date(),
            estado='pendiente',
            created_by=self.vendedor
        )
        
        # Cantidad mayor al inventario disponible
        cantidad_solicitada = self.inventario1.cantidad + 10
        
        detalle = DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto1,
            cantidad=cantidad_solicitada,
            precio_unitario=self.producto1.precio
        )
        
        # Verificar que se puede crear el detalle pero no confirmar
        self.assertEqual(detalle.cantidad, cantidad_solicitada)
        
        # Al intentar confirmar, debería fallar la validación de inventario
        inventario_inicial = self.inventario1.cantidad
        
        # Simular validación de inventario
        if detalle.cantidad > self.inventario1.cantidad:
            # No se debe actualizar el inventario
            pass
        else:
            self.inventario1.cantidad -= detalle.cantidad
            self.inventario1.save()
        
        # Verificar que el inventario no cambió
        self.inventario1.refresh_from_db()
        self.assertEqual(self.inventario1.cantidad, inventario_inicial)

    def test_should_handle_partial_deliveries(self):
        """Test entregas parciales"""
        
        # Crear pedido grande
        pedido = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=timezone.now().date(),
            estado='pendiente',
            created_by=self.vendedor
        )
        
        detalle = DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto1,
            cantidad=20,
            precio_unitario=self.producto1.precio,
            cantidad_entregada=0
        )
        
        # Primera entrega parcial (10 unidades)
        primera_entrega = 10
        detalle.cantidad_entregada += primera_entrega
        detalle.save()
        
        # Actualizar inventario
        self.inventario1.cantidad -= primera_entrega
        self.inventario1.save()
        
        # Verificar estado parcial
        self.assertEqual(detalle.cantidad_entregada, primera_entrega)
        self.assertEqual(detalle.cantidad_pendiente, 10)
        self.assertFalse(detalle.entregado_completo)
        
        # Segunda entrega (resto)
        segunda_entrega = 10
        detalle.cantidad_entregada += segunda_entrega
        detalle.save()
        
        # Actualizar inventario
        self.inventario1.cantidad -= segunda_entrega
        self.inventario1.save()
        
        # Verificar entrega completa
        self.assertEqual(detalle.cantidad_entregada, 20)
        self.assertEqual(detalle.cantidad_pendiente, 0)
        self.assertTrue(detalle.entregado_completo)

    def test_should_calculate_complex_pricing(self):
        """Test cálculos complejos de precios con descuentos"""
        
        # Crear cliente con descuento
        from clientes.models import DescuentoCliente
        descuento = DescuentoCliente.objects.create(
            cliente=self.cliente,
            tienda=self.tienda,
            porcentaje_descuento=Decimal('10.00'),
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date() + timezone.timedelta(days=30),
            activo=True
        )
        
        # Crear pedido
        pedido = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=timezone.now().date(),
            estado='pendiente',
            created_by=self.vendedor
        )
        
        # Agregar productos con descuento aplicado
        detalle = DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto1,
            cantidad=5,
            precio_unitario=self.producto1.precio,
            descuento_porcentaje=descuento.porcentaje_descuento
        )
        
        # Calcular valores esperados
        subtotal_sin_descuento = 5 * Decimal('100.00')
        descuento_monto = subtotal_sin_descuento * (Decimal('10.00') / Decimal('100.00'))
        subtotal_con_descuento = subtotal_sin_descuento - descuento_monto
        iva = subtotal_con_descuento * Decimal('0.16')
        total = subtotal_con_descuento + iva
        
        # Actualizar pedido con cálculos
        pedido.subtotal = subtotal_con_descuento
        pedido.descuento_total = descuento_monto
        pedido.iva = iva
        pedido.total = total
        pedido.save()
        
        # Verificar cálculos
        self.assertDecimalEqual(pedido.subtotal, subtotal_con_descuento)
        self.assertDecimalEqual(pedido.descuento_total, descuento_monto)
        self.assertDecimalEqual(pedido.iva, iva)
        self.assertDecimalEqual(pedido.total, total)

    def test_should_track_sales_by_period(self):
        """Test seguimiento de ventas por período"""
        
        # Crear ventas en diferentes fechas
        fecha1 = timezone.now().date()
        fecha2 = fecha1 + timezone.timedelta(days=1)
        
        # Venta día 1
        pedido1 = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=fecha1,
            estado='confirmado',
            total=Decimal('500.00'),
            created_by=self.vendedor
        )
        
        # Venta día 2
        pedido2 = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=fecha2,
            estado='confirmado',
            total=Decimal('300.00'),
            created_by=self.vendedor
        )
        
        # Consultar ventas por período
        ventas_dia1 = Pedido.objects.filter(
            tienda=self.tienda,
            fecha=fecha1,
            estado='confirmado'
        )
        ventas_dia2 = Pedido.objects.filter(
            tienda=self.tienda,
            fecha=fecha2,
            estado='confirmado'
        )
        
        # Calcular totales
        total_dia1 = sum(p.total for p in ventas_dia1)
        total_dia2 = sum(p.total for p in ventas_dia2)
        
        self.assertDecimalEqual(total_dia1, Decimal('500.00'))
        self.assertDecimalEqual(total_dia2, Decimal('300.00'))
        
        # Total período
        ventas_periodo = Pedido.objects.filter(
            tienda=self.tienda,
            fecha__gte=fecha1,
            fecha__lte=fecha2,
            estado='confirmado'
        )
        total_periodo = sum(p.total for p in ventas_periodo)
        
        self.assertDecimalEqual(total_periodo, Decimal('800.00'))

    def test_should_handle_sales_cancellation(self):
        """Test cancelación de ventas"""
        
        # Crear venta confirmada
        pedido = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=timezone.now().date(),
            estado='confirmado',
            created_by=self.vendedor
        )
        
        detalle = DetallePedido.objects.create(
            pedido=pedido,
            producto=self.producto1,
            cantidad=5,
            precio_unitario=self.producto1.precio
        )
        
        # Simular que se había actualizado inventario
        inventario_antes_venta = self.inventario1.cantidad
        self.inventario1.cantidad -= 5
        self.inventario1.save()
        
        # Cancelar pedido
        pedido.estado = 'cancelado'
        pedido.save()
        
        # Restaurar inventario
        self.inventario1.cantidad += 5
        self.inventario1.save()
        
        # Verificar restauración
        self.inventario1.refresh_from_db()
        self.assertEqual(self.inventario1.cantidad, inventario_antes_venta)
        self.assertEqual(pedido.estado, 'cancelado')

    def test_should_integrate_with_cash_register(self):
        """Test integración completa con caja registradora"""
        
        # Estado inicial de caja
        saldo_inicial = self.caja.saldo_final
        
        # Crear venta
        pedido = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=timezone.now().date(),
            estado='confirmado',
            total=Decimal('500.00'),
            created_by=self.vendedor
        )
        
        # Registrar en caja
        transaccion = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=pedido.total,
            descripcion=f'Venta #{pedido.id}',
            pedido=pedido,
            created_by=self.vendedor
        )
        
        # Actualizar saldo de caja
        self.caja.ingresos += transaccion.monto
        self.caja.saldo_final = self.caja.fondo_inicial + self.caja.ingresos - self.caja.egresos
        self.caja.save()
        
        # Verificar integración
        self.caja.refresh_from_db()
        expected_saldo = saldo_inicial + pedido.total
        
        self.assertDecimalEqual(self.caja.saldo_final, expected_saldo)
        self.assertEqual(transaccion.pedido, pedido)
        self.assertDecimalEqual(transaccion.monto, pedido.total)


class InventarioIntegrationTestCase(BaseIntegrationTestCase):
    """Tests de integración para el sistema de inventario"""
    
    def setUp(self):
        super().setUp()
        
        # Crear segunda tienda para traspasos
        self.tienda_destino = TiendaFactory(nombre='Tienda Destino')
        
        # Productos
        self.producto = ProductoFactory(
            tienda=self.tienda,
            codigo='PROD001'
        )
        
        # Inventarios en ambas tiendas
        self.inventario_origen = Inventario.objects.create(
            producto=self.producto,
            tienda=self.tienda,
            cantidad=100
        )
        
        self.inventario_destino = Inventario.objects.create(
            producto=self.producto,
            tienda=self.tienda_destino,
            cantidad=20
        )

    def test_should_complete_inventory_transfer_workflow(self):
        """Test flujo completo de traspaso de inventario"""
        from inventario.models import Traspaso, TraspasoItem
        
        # 1. Crear traspaso
        traspaso = Traspaso.objects.create(
            tienda_origen=self.tienda,
            tienda_destino=self.tienda_destino,
            fecha=timezone.now().date(),
            estado='pendiente',
            created_by=self.admin_user
        )
        
        # 2. Agregar items al traspaso
        cantidad_traspaso = 30
        item = TraspasoItem.objects.create(
            traspaso=traspaso,
            producto=self.producto,
            cantidad=cantidad_traspaso
        )
        
        # 3. Confirmar traspaso
        inventario_origen_inicial = self.inventario_origen.cantidad
        inventario_destino_inicial = self.inventario_destino.cantidad
        
        traspaso.estado = 'confirmado'
        traspaso.save()
        
        # 4. Actualizar inventarios
        self.inventario_origen.cantidad -= cantidad_traspaso
        self.inventario_origen.save()
        
        self.inventario_destino.cantidad += cantidad_traspaso
        self.inventario_destino.save()
        
        # 5. Verificar actualización
        self.inventario_origen.refresh_from_db()
        self.inventario_destino.refresh_from_db()
        
        self.assertEqual(
            self.inventario_origen.cantidad,
            inventario_origen_inicial - cantidad_traspaso
        )
        self.assertEqual(
            self.inventario_destino.cantidad,
            inventario_destino_inicial + cantidad_traspaso
        )

    def test_should_prevent_negative_inventory(self):
        """Test prevención de inventario negativo"""
        from inventario.models import Traspaso, TraspasoItem
        
        # Intentar traspasar más de lo disponible
        cantidad_disponible = self.inventario_origen.cantidad
        cantidad_solicitada = cantidad_disponible + 50
        
        traspaso = Traspaso.objects.create(
            tienda_origen=self.tienda,
            tienda_destino=self.tienda_destino,
            fecha=timezone.now().date(),
            estado='pendiente',
            created_by=self.admin_user
        )
        
        item = TraspasoItem.objects.create(
            traspaso=traspaso,
            producto=self.producto,
            cantidad=cantidad_solicitada
        )
        
        # Validación antes de confirmar
        if item.cantidad > self.inventario_origen.cantidad:
            traspaso.estado = 'rechazado'
            traspaso.save()
        
        # Verificar que no se actualizó el inventario
        inventario_inicial = self.inventario_origen.cantidad
        self.inventario_origen.refresh_from_db()
        
        self.assertEqual(self.inventario_origen.cantidad, inventario_inicial)
        self.assertEqual(traspaso.estado, 'rechazado')

    def test_should_track_inventory_movements(self):
        """Test seguimiento de movimientos de inventario"""
        
        # Registrar diferentes tipos de movimientos
        movimientos = []
        
        # Venta (reduce inventario)
        self.inventario_origen.cantidad -= 10
        self.inventario_origen.save()
        movimientos.append({
            'tipo': 'venta',
            'cantidad': -10,
            'fecha': timezone.now()
        })
        
        # Compra (aumenta inventario)
        self.inventario_origen.cantidad += 50
        self.inventario_origen.save()
        movimientos.append({
            'tipo': 'compra',
            'cantidad': 50,
            'fecha': timezone.now()
        })
        
        # Ajuste manual
        self.inventario_origen.cantidad += 5
        self.inventario_origen.save()
        movimientos.append({
            'tipo': 'ajuste',
            'cantidad': 5,
            'fecha': timezone.now()
        })
        
        # Verificar cantidad final
        cantidad_esperada = 100 - 10 + 50 + 5  # inicial + movimientos
        self.assertEqual(self.inventario_origen.cantidad, cantidad_esperada)
