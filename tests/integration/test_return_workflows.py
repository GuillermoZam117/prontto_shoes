"""
Tests de integración para flujos completos de devoluciones
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from tests.base_simple import BaseIntegrationTestCase
from tests.factories import (
    TiendaFactory, ProductoFactory, ClienteFactory, UserFactory,
    PedidoFactory, DetallePedidoFactory, ProveedorFactory
)

from devoluciones.models import Devolucion
from ventas.models import Pedido, DetallePedido
from productos.models import Producto
from inventario.models import Inventario
from caja.models import TransaccionCaja
from clientes.models import Anticipo


class DevolucionesIntegrationTestCase(BaseIntegrationTestCase):
    """Tests de integración para el sistema de devoluciones"""
    
    def setUp(self):
        super().setUp()
        
        # Proveedor
        self.proveedor = ProveedorFactory()
        
        # Productos
        self.producto1 = ProductoFactory(
            tienda=self.tienda,
            codigo='PROD001',
            precio=Decimal('100.00'),
            proveedor=self.proveedor
        )
        self.producto2 = ProductoFactory(
            tienda=self.tienda,
            codigo='PROD002',
            precio=Decimal('200.00'),
            proveedor=self.proveedor
        )
        
        # Inventarios
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
        
        # Usuario
        self.vendedor = UserFactory(username='vendedor')
        
        # Venta original para devoluciones
        self.pedido_original = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=timezone.now().date(),
            estado='confirmado',
            created_by=self.vendedor
        )
        
        self.detalle_original = DetallePedido.objects.create(
            pedido=self.pedido_original,
            producto=self.producto1,
            cantidad=5,
            precio_unitario=self.producto1.precio
        )
        
        # Actualizar totales del pedido
        self.pedido_original.subtotal = Decimal('431.03')  # 500 / 1.16
        self.pedido_original.iva = Decimal('68.97')
        self.pedido_original.total = Decimal('500.00')
        self.pedido_original.save()

    def test_should_complete_customer_return_workflow(self):
        """Test flujo completo de devolución por defecto del cliente"""
        
        # 1. Cliente reporta producto defectuoso
        devolucion = Devolucion.objects.create(
            tipo='defecto',
            pedido_original=self.pedido_original,
            producto=self.producto1,
            cantidad=2,  # Devuelve 2 de 5
            motivo='Producto llegó dañado',
            estado='pendiente',
            created_by=self.vendedor
        )
        
        # 2. Revisar producto devuelto
        devolucion.estado = 'revision'
        devolucion.save()
        
        # 3. Aprobar devolución
        devolucion.estado = 'aprobada'
        devolucion.fecha_aprobacion = timezone.now().date()
        devolucion.save()
        
        # 4. Calcular monto de devolución
        monto_unitario = self.detalle_original.precio_unitario
        subtotal_devolucion = monto_unitario * devolucion.cantidad
        iva_devolucion = subtotal_devolucion * Decimal('0.16')
        total_devolucion = subtotal_devolucion + iva_devolucion
        
        devolucion.monto_devolucion = total_devolucion
        devolucion.save()
        
        # 5. Actualizar inventario (producto defectuoso no regresa a stock)
        # Para productos defectuosos, no se actualiza inventario
        inventario_inicial = self.inventario1.cantidad
        
        # 6. Generar saldo a favor del cliente
        if devolucion.tipo == 'defecto':
            saldo_a_favor = Anticipo.objects.create(
                cliente=self.cliente,
                tienda=self.tienda,
                monto=total_devolucion,
                fecha=timezone.now().date(),
                estado='aprobado',
                created_by=self.vendedor
            )
            
            devolucion.saldo_a_favor = saldo_a_favor
            devolucion.save()
        
        # 7. Registrar egreso en caja
        transaccion = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='EGRESO',
            monto=total_devolucion,
            descripcion=f'Devolución #{devolucion.id} - {devolucion.motivo}',
            anticipo=saldo_a_favor,
            created_by=self.vendedor
        )
        
        # 8. Finalizar devolución
        devolucion.estado = 'completada'
        devolucion.save()
        
        # Verificaciones
        self.assertEqual(devolucion.estado, 'completada')
        self.assertDecimalEqual(devolucion.monto_devolucion, Decimal('232.00'))  # 200 * 1.16
        self.assertEqual(self.inventario1.cantidad, inventario_inicial)  # No cambia por defecto
        self.assertIsNotNone(devolucion.saldo_a_favor)
        self.assertEqual(transaccion.anticipo, saldo_a_favor)

    def test_should_complete_exchange_return_workflow(self):
        """Test flujo completo de devolución por cambio"""
        
        # 1. Cliente solicita cambio de producto
        devolucion = Devolucion.objects.create(
            tipo='cambio',
            pedido_original=self.pedido_original,
            producto=self.producto1,
            cantidad=3,
            motivo='Cliente quiere producto diferente',
            estado='pendiente',
            created_by=self.vendedor
        )
        
        # 2. Aprobar cambio
        devolucion.estado = 'aprobada'
        devolucion.fecha_aprobacion = timezone.now().date()
        devolucion.save()
        
        # 3. Producto regresa a inventario (está en buen estado)
        inventario_inicial = self.inventario1.cantidad
        self.inventario1.cantidad += devolucion.cantidad
        self.inventario1.save()
        
        # 4. Cliente elige nuevo producto
        nuevo_pedido = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=timezone.now().date(),
            estado='confirmado',
            created_by=self.vendedor
        )
        
        nuevo_detalle = DetallePedido.objects.create(
            pedido=nuevo_pedido,
            producto=self.producto2,  # Producto diferente
            cantidad=2,
            precio_unitario=self.producto2.precio
        )
        
        # 5. Calcular diferencia de precios
        valor_devuelto = self.producto1.precio * devolucion.cantidad  # 300.00
        valor_nuevo = self.producto2.precio * nuevo_detalle.cantidad  # 400.00
        diferencia = valor_nuevo - valor_devuelto  # 100.00
        
        # 6. Cliente paga diferencia
        if diferencia > 0:
            transaccion_diferencia = TransaccionCaja.objects.create(
                caja=self.caja,
                tipo_movimiento='INGRESO',
                monto=diferencia * Decimal('1.16'),  # Con IVA
                descripcion=f'Diferencia por cambio - Devolución #{devolucion.id}',
                pedido=nuevo_pedido,
                created_by=self.vendedor
            )
        
        # 7. Vincular devolución con nuevo pedido
        devolucion.pedido_cambio = nuevo_pedido
        devolucion.estado = 'completada'
        devolucion.save()
        
        # 8. Actualizar inventario del nuevo producto
        self.inventario2.cantidad -= nuevo_detalle.cantidad
        self.inventario2.save()
        
        # Verificaciones
        self.assertEqual(devolucion.estado, 'completada')
        self.assertEqual(devolucion.pedido_cambio, nuevo_pedido)
        self.assertEqual(self.inventario1.cantidad, inventario_inicial + 3)  # Regresó a stock
        self.assertEqual(self.inventario2.cantidad, 28)  # Se vendieron 2
        self.assertDecimalEqual(transaccion_diferencia.monto, Decimal('116.00'))  # 100 * 1.16

    def test_should_handle_supplier_return_workflow(self):
        """Test flujo de devolución a proveedor"""
        
        # 1. Detectar producto defectuoso en lote
        devolucion = Devolucion.objects.create(
            tipo='defecto',
            proveedor=self.proveedor,
            producto=self.producto1,
            cantidad=10,  # Lote defectuoso
            motivo='Lote completo defectuoso - devolución a proveedor',
            estado='pendiente',
            requiere_aprobacion_proveedor=True,
            created_by=self.admin_user
        )
        
        # 2. Documentar devolución
        devolucion.estado = 'documentada'
        devolucion.save()
        
        # 3. Enviar a proveedor
        devolucion.estado = 'enviada_proveedor'
        devolucion.fecha_envio_proveedor = timezone.now().date()
        devolucion.save()
        
        # 4. Proveedor confirma recepción
        devolucion.estado = 'confirmada_proveedor'
        devolucion.fecha_confirmacion_proveedor = timezone.now().date()
        devolucion.save()
        
        # 5. Actualizar inventario (sacar productos defectuosos)
        inventario_inicial = self.inventario1.cantidad
        self.inventario1.cantidad -= devolucion.cantidad
        self.inventario1.save()
        
        # 6. Proveedor aprueba crédito
        monto_credito = devolucion.cantidad * (self.producto1.precio * Decimal('0.7'))  # Precio de costo
        devolucion.monto_credito_proveedor = monto_credito
        devolucion.estado = 'credito_aprobado'
        devolucion.save()
        
        # 7. Finalizar devolución
        devolucion.estado = 'completada'
        devolucion.save()
        
        # Verificaciones
        self.assertEqual(devolucion.estado, 'completada')
        self.assertTrue(devolucion.requiere_aprobacion_proveedor)
        self.assertIsNotNone(devolucion.fecha_confirmacion_proveedor)
        self.assertDecimalEqual(devolucion.monto_credito_proveedor, Decimal('700.00'))  # 10 * 100 * 0.7
        self.assertEqual(self.inventario1.cantidad, inventario_inicial - 10)

    def test_should_handle_partial_returns(self):
        """Test devoluciones parciales"""
        
        # Pedido original con múltiples productos
        detalle2 = DetallePedido.objects.create(
            pedido=self.pedido_original,
            producto=self.producto2,
            cantidad=3,
            precio_unitario=self.producto2.precio
        )
        
        # Primera devolución parcial
        devolucion1 = Devolucion.objects.create(
            tipo='defecto',
            pedido_original=self.pedido_original,
            producto=self.producto1,
            cantidad=2,  # Solo 2 de 5
            motivo='Algunos productos defectuosos',
            estado='aprobada',
            created_by=self.vendedor
        )
        
        # Calcular monto primera devolución
        monto1 = (self.producto1.precio * 2) * Decimal('1.16')
        devolucion1.monto_devolucion = monto1
        devolucion1.estado = 'completada'
        devolucion1.save()
        
        # Segunda devolución parcial (mismo pedido, producto diferente)
        devolucion2 = Devolucion.objects.create(
            tipo='cambio',
            pedido_original=self.pedido_original,
            producto=self.producto2,
            cantidad=1,  # Solo 1 de 3
            motivo='Cliente no le gustó el color',
            estado='aprobada',
            created_by=self.vendedor
        )
        
        # Producto regresa a inventario
        inventario2_inicial = self.inventario2.cantidad
        self.inventario2.cantidad += 1
        self.inventario2.save()
        
        monto2 = (self.producto2.precio * 1) * Decimal('1.16')
        devolucion2.monto_devolucion = monto2
        devolucion2.estado = 'completada'
        devolucion2.save()
        
        # Verificar devoluciones parciales
        devoluciones_pedido = Devolucion.objects.filter(pedido_original=self.pedido_original)
        total_devuelto = sum(d.monto_devolucion for d in devoluciones_pedido)
        
        self.assertEqual(devoluciones_pedido.count(), 2)
        self.assertDecimalEqual(total_devuelto, monto1 + monto2)
        self.assertEqual(self.inventario2.cantidad, inventario2_inicial + 1)

    def test_should_track_return_statistics(self):
        """Test seguimiento de estadísticas de devoluciones"""
        
        # Crear múltiples devoluciones en el mes
        fecha_base = timezone.now().date()
        
        devoluciones_mes = []
        
        # Devoluciones por defecto
        for i in range(3):
            dev = Devolucion.objects.create(
                tipo='defecto',
                producto=self.producto1,
                cantidad=1,
                motivo=f'Defecto #{i+1}',
                estado='completada',
                monto_devolucion=Decimal('116.00'),
                created_by=self.vendedor
            )
            devoluciones_mes.append(dev)
        
        # Devoluciones por cambio
        for i in range(2):
            dev = Devolucion.objects.create(
                tipo='cambio',
                producto=self.producto2,
                cantidad=1,
                motivo=f'Cambio #{i+1}',
                estado='completada',
                monto_devolucion=Decimal('232.00'),
                created_by=self.vendedor
            )
            devoluciones_mes.append(dev)
        
        # Calcular estadísticas
        total_devoluciones = len(devoluciones_mes)
        devoluciones_defecto = len([d for d in devoluciones_mes if d.tipo == 'defecto'])
        devoluciones_cambio = len([d for d in devoluciones_mes if d.tipo == 'cambio'])
        
        monto_total_devuelto = sum(d.monto_devolucion for d in devoluciones_mes)
        
        # Estadísticas por producto
        devoluciones_producto1 = len([d for d in devoluciones_mes if d.producto == self.producto1])
        devoluciones_producto2 = len([d for d in devoluciones_mes if d.producto == self.producto2])
        
        # Verificar estadísticas
        self.assertEqual(total_devoluciones, 5)
        self.assertEqual(devoluciones_defecto, 3)
        self.assertEqual(devoluciones_cambio, 2)
        self.assertDecimalEqual(monto_total_devuelto, Decimal('812.00'))  # 3*116 + 2*232
        self.assertEqual(devoluciones_producto1, 3)
        self.assertEqual(devoluciones_producto2, 2)

    def test_should_validate_return_timeframe(self):
        """Test validación de tiempo límite para devoluciones"""
        
        # Pedido muy antiguo (más de 30 días)
        fecha_antigua = timezone.now().date() - timezone.timedelta(days=35)
        pedido_antiguo = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=fecha_antigua,
            estado='confirmado',
            created_by=self.vendedor
        )
        
        # Intentar crear devolución
        dias_transcurridos = (timezone.now().date() - pedido_antiguo.fecha).days
        limite_devolucion = 30  # días
        
        if dias_transcurridos > limite_devolucion:
            # Devolución requiere aprobación especial
            devolucion = Devolucion.objects.create(
                tipo='defecto',
                pedido_original=pedido_antiguo,
                producto=self.producto1,
                cantidad=1,
                motivo='Producto defectuoso - fuera de tiempo',
                estado='requiere_aprobacion_especial',
                created_by=self.vendedor
            )
        else:
            # Devolución normal
            devolucion = Devolucion.objects.create(
                tipo='defecto',
                pedido_original=self.pedido_original,
                producto=self.producto1,
                cantidad=1,
                motivo='Producto defectuoso - en tiempo',
                estado='pendiente',
                created_by=self.vendedor
            )
        
        # Verificar validación de tiempo
        devolucion_antigua = Devolucion.objects.get(pedido_original=pedido_antiguo)
        self.assertEqual(devolucion_antigua.estado, 'requiere_aprobacion_especial')

    def test_should_integrate_returns_with_loyalty_program(self):
        """Test integración con programa de lealtad"""
        from clientes.models import ReglaProgramaLealtad
        
        # Configurar programa de lealtad
        regla_lealtad = ReglaProgramaLealtad.objects.create(
            tienda=self.tienda,
            puntos_por_peso=Decimal('1.0'),  # 1 punto por peso gastado
            activa=True
        )
        
        # Cliente tenía puntos por la compra original
        puntos_ganados_original = int(self.pedido_original.total)
        self.cliente.puntos_lealtad = puntos_ganados_original
        self.cliente.save()
        
        # Devolución por defecto
        devolucion = Devolucion.objects.create(
            tipo='defecto',
            pedido_original=self.pedido_original,
            producto=self.producto1,
            cantidad=2,
            monto_devolucion=Decimal('232.00'),
            estado='completada',
            created_by=self.vendedor
        )
        
        # Descontar puntos por devolución
        puntos_a_descontar = int(devolucion.monto_devolucion)
        self.cliente.puntos_lealtad -= puntos_a_descontar
        self.cliente.save()
        
        # Verificar ajuste de puntos
        puntos_esperados = puntos_ganados_original - puntos_a_descontar
        self.assertEqual(self.cliente.puntos_lealtad, puntos_esperados)
