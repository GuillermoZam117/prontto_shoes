"""
Tests de integración para operaciones completas de caja
"""
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from tests.base_simple import BaseIntegrationTestCase
from tests.factories import (
    TiendaFactory, UserFactory, CajaFactory, ClienteFactory,
    PedidoFactory, AnticipoFactory
)

from caja.models import Caja, TransaccionCaja, NotaCargo, Factura
from ventas.models import Pedido
from clientes.models import Anticipo


class CajaIntegrationTestCase(BaseIntegrationTestCase):
    """Tests de integración para operaciones de caja"""
    
    def setUp(self):
        super().setUp()
        
        # Usuario cajero
        self.cajero = UserFactory(username='cajero')
        
        # Cliente
        self.cliente = ClienteFactory(tienda=self.tienda)
        
        # Caja con fondo inicial
        self.caja.fondo_inicial = Decimal('1000.00')
        self.caja.saldo_final = Decimal('1000.00')
        self.caja.save()

    def test_should_complete_daily_cash_cycle(self):
        """Test ciclo completo diario de caja"""
        
        # 1. Apertura de caja (ya está abierta)
        self.assertFalse(self.caja.cerrada)
        self.assertDecimalEqual(self.caja.saldo_final, Decimal('1000.00'))
        
        # 2. Registrar ventas
        venta1 = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('250.00'),
            descripcion='Venta producto A',
            created_by=self.cajero
        )
        
        venta2 = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('150.00'),
            descripcion='Venta producto B',
            created_by=self.cajero
        )
        
        # 3. Registrar gastos
        gasto1 = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='EGRESO',
            monto=Decimal('50.00'),
            descripcion='Compra materiales oficina',
            created_by=self.cajero
        )
        
        # 4. Actualizar totales de caja
        self.caja.ingresos = Decimal('400.00')  # 250 + 150
        self.caja.egresos = Decimal('50.00')
        self.caja.saldo_final = self.caja.fondo_inicial + self.caja.ingresos - self.caja.egresos
        self.caja.save()
        
        # 5. Verificar cálculos
        expected_saldo = Decimal('1000.00') + Decimal('400.00') - Decimal('50.00')
        self.assertDecimalEqual(self.caja.saldo_final, expected_saldo)
        
        # 6. Cierre de caja
        self.caja.cerrada = True
        self.caja.save()
        
        # Verificar cierre
        self.assertTrue(self.caja.cerrada)
        self.assertDecimalEqual(self.caja.saldo_final, Decimal('1350.00'))

    def test_should_handle_cash_advances_workflow(self):
        """Test flujo completo de anticipos"""
        
        # 1. Cliente solicita anticipo
        anticipo = Anticipo.objects.create(
            cliente=self.cliente,
            tienda=self.tienda,
            monto=Decimal('500.00'),
            fecha=timezone.now().date(),
            estado='pendiente',
            created_by=self.cajero
        )
        
        # 2. Registrar anticipo en caja (egreso)
        transaccion_anticipo = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='EGRESO',
            monto=anticipo.monto,
            descripcion=f'Anticipo cliente {self.cliente.nombre}',
            anticipo=anticipo,
            created_by=self.cajero
        )
        
        # 3. Confirmar anticipo
        anticipo.estado = 'aprobado'
        anticipo.save()
        
        # 4. Actualizar caja
        self.caja.egresos += anticipo.monto
        self.caja.saldo_final = self.caja.fondo_inicial + self.caja.ingresos - self.caja.egresos
        self.caja.save()
        
        # Verificar anticipo
        saldo_esperado = Decimal('1000.00') - Decimal('500.00')
        self.assertDecimalEqual(self.caja.saldo_final, saldo_esperado)
        self.assertEqual(anticipo.estado, 'aprobado')
        self.assertEqual(transaccion_anticipo.anticipo, anticipo)
        
        # 5. Cliente paga anticipo con compra
        pedido = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=timezone.now().date(),
            total=Decimal('600.00'),
            estado='confirmado',
            created_by=self.cajero
        )
        
        # 6. Aplicar anticipo al pedido
        monto_a_pagar = pedido.total - anticipo.monto
        
        # Registrar pago restante
        transaccion_pago = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=monto_a_pagar,
            descripcion=f'Pago pedido {pedido.id} (con anticipo)',
            pedido=pedido,
            created_by=self.cajero
        )
        
        # 7. Marcar anticipo como utilizado
        anticipo.estado = 'utilizado'
        anticipo.pedido = pedido
        anticipo.save()
        
        # Verificar flujo completo
        self.assertEqual(anticipo.estado, 'utilizado')
        self.assertEqual(anticipo.pedido, pedido)
        self.assertDecimalEqual(transaccion_pago.monto, Decimal('100.00'))

    def test_should_handle_charge_notes_workflow(self):
        """Test flujo de notas de cargo"""
        
        # 1. Crear nota de cargo por faltante
        nota_cargo = NotaCargo.objects.create(
            caja=self.caja,
            monto=Decimal('25.00'),
            motivo='Faltante en caja al cierre',
            fecha=timezone.now().date(),
            created_by=self.cajero
        )
        
        # 2. Registrar nota de cargo en transacciones
        transaccion_cargo = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='EGRESO',
            monto=nota_cargo.monto,
            descripcion=f'Nota de cargo: {nota_cargo.motivo}',
            nota_cargo=nota_cargo,
            created_by=self.cajero
        )
        
        # 3. Actualizar caja
        self.caja.egresos += nota_cargo.monto
        self.caja.saldo_final = self.caja.fondo_inicial + self.caja.ingresos - self.caja.egresos
        self.caja.save()
        
        # Verificar nota de cargo
        saldo_esperado = Decimal('1000.00') - Decimal('25.00')
        self.assertDecimalEqual(self.caja.saldo_final, saldo_esperado)
        self.assertEqual(transaccion_cargo.nota_cargo, nota_cargo)
        self.assertDecimalEqual(transaccion_cargo.monto, nota_cargo.monto)

    def test_should_generate_invoices_workflow(self):
        """Test flujo de generación de facturas"""
        
        # 1. Crear venta que requiere factura
        pedido = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=timezone.now().date(),
            total=Decimal('1000.00'),
            estado='confirmado',
            created_by=self.cajero
        )
        
        # 2. Registrar venta en caja
        transaccion_venta = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=pedido.total,
            descripcion=f'Venta pedido {pedido.id}',
            pedido=pedido,
            created_by=self.cajero
        )
        
        # 3. Generar factura
        factura = Factura.objects.create(
            pedido=pedido,
            numero='F001-001',
            fecha=timezone.now().date(),
            subtotal=Decimal('862.07'),  # 1000 / 1.16
            iva=Decimal('137.93'),       # 1000 - 862.07
            total=pedido.total,
            created_by=self.cajero
        )
        
        # 4. Verificar factura
        self.assertEqual(factura.pedido, pedido)
        self.assertDecimalEqual(factura.total, pedido.total)
        self.assertDecimalEqual(factura.subtotal + factura.iva, factura.total)
        
        # 5. Verificar relación con transacción
        self.assertEqual(transaccion_venta.pedido, pedido)
        self.assertEqual(transaccion_venta.pedido.factura_set.first(), factura)

    def test_should_handle_cash_discrepancies(self):
        """Test manejo de diferencias en caja"""
        
        # Simular ventas registradas
        total_ventas = Decimal('800.00')
        self.caja.ingresos = total_ventas
        self.caja.saldo_final = self.caja.fondo_inicial + self.caja.ingresos
        self.caja.save()
        
        # Conteo físico de caja
        conteo_fisico = Decimal('1750.00')  # Faltante de 50.00
        diferencia = conteo_fisico - self.caja.saldo_final
        
        if diferencia != 0:
            # Crear nota de cargo por la diferencia
            if diferencia < 0:
                nota_cargo = NotaCargo.objects.create(
                    caja=self.caja,
                    monto=abs(diferencia),
                    motivo='Faltante en conteo físico',
                    fecha=timezone.now().date(),
                    created_by=self.cajero
                )
                
                # Registrar en transacciones
                TransaccionCaja.objects.create(
                    caja=self.caja,
                    tipo_movimiento='EGRESO',
                    monto=abs(diferencia),
                    descripcion='Ajuste por faltante en caja',
                    nota_cargo=nota_cargo,
                    created_by=self.cajero
                )
                
                # Actualizar saldo
                self.caja.egresos += abs(diferencia)
            else:
                # Sobrante - registrar como ingreso
                TransaccionCaja.objects.create(
                    caja=self.caja,
                    tipo_movimiento='INGRESO',
                    monto=diferencia,
                    descripcion='Ajuste por sobrante en caja',
                    created_by=self.cajero
                )
                
                self.caja.ingresos += diferencia
            
            # Actualizar saldo final
            self.caja.saldo_final = self.caja.fondo_inicial + self.caja.ingresos - self.caja.egresos
            self.caja.save()
        
        # Verificar ajuste
        self.assertDecimalEqual(self.caja.saldo_final, conteo_fisico)

    def test_should_track_multiple_payment_methods(self):
        """Test seguimiento de múltiples métodos de pago"""
        
        # Venta con pago mixto
        pedido = Pedido.objects.create(
            tienda=self.tienda,
            cliente=self.cliente,
            fecha=timezone.now().date(),
            total=Decimal('500.00'),
            estado='confirmado',
            created_by=self.cajero
        )
        
        # Pago en efectivo
        pago_efectivo = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('300.00'),
            descripcion='Pago efectivo pedido {}'.format(pedido.id),
            referencia='EFECTIVO',
            pedido=pedido,
            created_by=self.cajero
        )
        
        # Pago con tarjeta (no afecta caja física)
        pago_tarjeta = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('200.00'),
            descripcion='Pago tarjeta pedido {}'.format(pedido.id),
            referencia='TARJETA',
            pedido=pedido,
            created_by=self.cajero
        )
        
        # Actualizar solo efectivo en caja física
        self.caja.ingresos += pago_efectivo.monto  # Solo efectivo
        self.caja.saldo_final = self.caja.fondo_inicial + self.caja.ingresos - self.caja.egresos
        self.caja.save()
        
        # Verificar transacciones
        transacciones_pedido = TransaccionCaja.objects.filter(pedido=pedido)
        total_transacciones = sum(t.monto for t in transacciones_pedido)
        
        self.assertEqual(transacciones_pedido.count(), 2)
        self.assertDecimalEqual(total_transacciones, pedido.total)
        self.assertDecimalEqual(self.caja.saldo_final, Decimal('1300.00'))  # 1000 + 300

    def test_should_handle_cash_transfers_between_boxes(self):
        """Test transferencias entre cajas"""
        
        # Crear segunda caja
        caja2 = CajaFactory(
            tienda=self.tienda,
            fecha=timezone.now().date(),
            fondo_inicial=Decimal('500.00'),
            saldo_final=Decimal('500.00')
        )
        
        # Transferencia de caja1 a caja2
        monto_transferencia = Decimal('200.00')
        
        # Egreso de caja origen
        egreso = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='EGRESO',
            monto=monto_transferencia,
            descripcion=f'Transferencia a caja {caja2.id}',
            referencia=f'TRANSFER_TO_{caja2.id}',
            created_by=self.cajero
        )
        
        # Ingreso en caja destino
        ingreso = TransaccionCaja.objects.create(
            caja=caja2,
            tipo_movimiento='INGRESO',
            monto=monto_transferencia,
            descripcion=f'Transferencia desde caja {self.caja.id}',
            referencia=f'TRANSFER_FROM_{self.caja.id}',
            created_by=self.cajero
        )
        
        # Actualizar saldos
        self.caja.egresos += monto_transferencia
        self.caja.saldo_final = self.caja.fondo_inicial + self.caja.ingresos - self.caja.egresos
        self.caja.save()
        
        caja2.ingresos += monto_transferencia
        caja2.saldo_final = caja2.fondo_inicial + caja2.ingresos - caja2.egresos
        caja2.save()
        
        # Verificar transferencia
        self.assertDecimalEqual(self.caja.saldo_final, Decimal('800.00'))  # 1000 - 200
        self.assertDecimalEqual(caja2.saldo_final, Decimal('700.00'))      # 500 + 200
        
        # Verificar referencias cruzadas
        self.assertEqual(egreso.referencia, f'TRANSFER_TO_{caja2.id}')
        self.assertEqual(ingreso.referencia, f'TRANSFER_FROM_{self.caja.id}')

    def test_should_generate_daily_cash_report(self):
        """Test generación de reporte diario de caja"""
        
        # Registrar diferentes transacciones
        transacciones_del_dia = []
        
        # Ventas
        for i in range(3):
            t = TransaccionCaja.objects.create(
                caja=self.caja,
                tipo_movimiento='INGRESO',
                monto=Decimal(f'{100 + i * 50}.00'),
                descripcion=f'Venta #{i+1}',
                created_by=self.cajero
            )
            transacciones_del_dia.append(t)
        
        # Gastos
        for i in range(2):
            t = TransaccionCaja.objects.create(
                caja=self.caja,
                tipo_movimiento='EGRESO',
                monto=Decimal(f'{25 + i * 15}.00'),
                descripcion=f'Gasto #{i+1}',
                created_by=self.cajero
            )
            transacciones_del_dia.append(t)
        
        # Calcular totales
        total_ingresos = sum(
            t.monto for t in transacciones_del_dia 
            if t.tipo_movimiento == 'INGRESO'
        )
        total_egresos = sum(
            t.monto for t in transacciones_del_dia 
            if t.tipo_movimiento == 'EGRESO'
        )
        
        # Actualizar caja
        self.caja.ingresos = total_ingresos
        self.caja.egresos = total_egresos
        self.caja.saldo_final = self.caja.fondo_inicial + self.caja.ingresos - self.caja.egresos
        self.caja.save()
        
        # Generar reporte
        reporte = {
            'fecha': self.caja.fecha,
            'fondo_inicial': self.caja.fondo_inicial,
            'total_ingresos': total_ingresos,
            'total_egresos': total_egresos,
            'saldo_final': self.caja.saldo_final,
            'num_transacciones': len(transacciones_del_dia)
        }
        
        # Verificar reporte
        self.assertDecimalEqual(reporte['total_ingresos'], Decimal('450.00'))  # 100+150+200
        self.assertDecimalEqual(reporte['total_egresos'], Decimal('65.00'))    # 25+40
        self.assertDecimalEqual(reporte['saldo_final'], Decimal('1385.00'))    # 1000+450-65
        self.assertEqual(reporte['num_transacciones'], 5)
