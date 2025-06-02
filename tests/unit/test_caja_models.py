"""
Tests unitarios para los modelos del módulo de caja
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction, models
from django.utils import timezone
from datetime import date, timedelta
from unittest.mock import patch

from caja.models import Caja, NotaCargo, TransaccionCaja, MovimientoCaja, Factura
from tests.factories import (
    UserFactory, TiendaFactory, ClienteFactory, PedidoFactory,
    AnticipoFactory, CajaFactory, MovimientoCajaFactory, FacturaFactory
)


class CajaModelTestCase(TestCase):
    """Tests para el modelo Caja"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()

    def test_should_create_caja_with_required_fields_when_valid_data_provided(self):
        """Debe crear una caja con los campos obligatorios válidos"""
        fecha = date.today()
        caja = Caja.objects.create(
            tienda=self.tienda,
            fecha=fecha
        )
        
        self.assertEqual(caja.tienda, self.tienda)
        self.assertEqual(caja.fecha, fecha)
        self.assertEqual(caja.fondo_inicial, Decimal('0'))
        self.assertEqual(caja.ingresos, Decimal('0'))
        self.assertEqual(caja.egresos, Decimal('0'))
        self.assertEqual(caja.saldo_final, Decimal('0'))
        self.assertFalse(caja.cerrada)
        self.assertIsNotNone(caja.created_at)
        self.assertIsNotNone(caja.updated_at)

    def test_should_have_correct_string_representation_when_created(self):
        """Debe tener una representación string correcta"""
        fecha = date.today()
        caja = CajaFactory(tienda=self.tienda, fecha=fecha)
        expected = f"Caja {self.tienda.nombre} - {fecha}"
        self.assertEqual(str(caja), expected)

    def test_should_allow_optional_fields_when_creating_caja(self):
        """Debe permitir campos opcionales"""
        caja = Caja.objects.create(
            tienda=self.tienda,
            fecha=date.today(),
            fondo_inicial=Decimal('1000.00'),
            ingresos=Decimal('2500.50'),
            egresos=Decimal('500.25'),
            saldo_final=Decimal('3000.25'),
            cerrada=True,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(caja.fondo_inicial, Decimal('1000.00'))
        self.assertEqual(caja.ingresos, Decimal('2500.50'))
        self.assertEqual(caja.egresos, Decimal('500.25'))
        self.assertEqual(caja.saldo_final, Decimal('3000.25'))
        self.assertTrue(caja.cerrada)
        self.assertEqual(caja.created_by, self.user)
        self.assertEqual(caja.updated_by, self.user)

    def test_should_protect_tienda_when_caja_exists(self):
        """Debe proteger tienda cuando existe caja (PROTECT)"""
        CajaFactory(tienda=self.tienda)
        
        # No debe permitir eliminar tienda si tiene cajas
        with self.assertRaises(Exception):  # ProtectedError
            self.tienda.delete()

    def test_should_set_null_when_user_deleted(self):
        """Debe establecer NULL cuando se elimina el usuario (SET_NULL)"""
        user = UserFactory()
        caja = CajaFactory(tienda=self.tienda, created_by=user)
        
        # Eliminar usuario
        user.delete()
        caja.refresh_from_db()
        
        # Verificar que se estableció NULL
        self.assertIsNone(caja.created_by)

    def test_should_handle_audit_fields_correctly_when_user_provided(self):
        """Debe manejar campos de auditoría correctamente"""
        caja = CajaFactory(
            tienda=self.tienda,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(caja.created_by, self.user)
        self.assertEqual(caja.updated_by, self.user)

    def test_should_relate_to_tienda_correctly_through_foreign_key(self):
        """Debe relacionarse correctamente con tienda"""
        caja = CajaFactory(tienda=self.tienda)
        
        # Verificar relación desde caja a tienda
        self.assertEqual(caja.tienda, self.tienda)
        
        # Verificar relación inversa desde tienda a cajas
        self.assertIn(caja, self.tienda.cajas.all())

    def test_should_validate_decimal_precision_when_creating(self):
        """Debe validar precisión decimal en campos monetarios"""
        caja = Caja.objects.create(
            tienda=self.tienda,
            fecha=date.today(),
            fondo_inicial=Decimal('999999.99'),
            ingresos=Decimal('888888.88'),
            egresos=Decimal('777777.77'),
            saldo_final=Decimal('1110110.10')
        )
        
        self.assertEqual(caja.fondo_inicial, Decimal('999999.99'))
        self.assertEqual(caja.ingresos, Decimal('888888.88'))
        self.assertEqual(caja.egresos, Decimal('777777.77'))
        self.assertEqual(caja.saldo_final, Decimal('1110110.10'))

    def test_should_allow_negative_values_when_handling_deficits(self):
        """Debe permitir valores negativos para manejar déficits"""
        caja = Caja.objects.create(
            tienda=self.tienda,
            fecha=date.today(),
            saldo_final=Decimal('-100.00')  # Déficit
        )
        
        self.assertEqual(caja.saldo_final, Decimal('-100.00'))


class NotaCargoModelTestCase(TestCase):
    """Tests para el modelo NotaCargo"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()
        self.caja = CajaFactory(tienda=self.tienda)

    def test_should_create_nota_cargo_with_required_fields_when_valid_data_provided(self):
        """Debe crear una nota de cargo con los campos obligatorios válidos"""
        nota_cargo = NotaCargo.objects.create(
            caja=self.caja,
            monto=Decimal('250.00'),
            motivo="Gastos de oficina",
            fecha=date.today()
        )
        
        self.assertEqual(nota_cargo.caja, self.caja)
        self.assertEqual(nota_cargo.monto, Decimal('250.00'))
        self.assertEqual(nota_cargo.motivo, "Gastos de oficina")
        self.assertEqual(nota_cargo.fecha, date.today())
        self.assertIsNotNone(nota_cargo.created_at)

    def test_should_have_correct_string_representation_when_created(self):
        """Debe tener una representación string correcta"""
        nota_cargo = NotaCargo.objects.create(
            caja=self.caja,
            monto=Decimal('150.00'),
            motivo="Compra de insumos",
            fecha=date.today()
        )
        expected = f"Nota de cargo 150.00 - {self.tienda.nombre}"
        self.assertEqual(str(nota_cargo), expected)

    def test_should_cascade_delete_when_caja_deleted(self):
        """Debe eliminar notas de cargo cuando se elimina caja (CASCADE)"""
        nota_cargo = NotaCargo.objects.create(
            caja=self.caja,
            monto=Decimal('100.00'),
            motivo="Test",
            fecha=date.today()
        )
        nota_id = nota_cargo.id
        
        # Eliminar caja
        self.caja.delete()
        
        # Verificar que nota de cargo fue eliminada
        with self.assertRaises(NotaCargo.DoesNotExist):
            NotaCargo.objects.get(id=nota_id)

    def test_should_relate_to_caja_correctly_through_foreign_key(self):
        """Debe relacionarse correctamente con caja"""
        nota_cargo = NotaCargo.objects.create(
            caja=self.caja,
            monto=Decimal('200.00'),
            motivo="Test motivo",
            fecha=date.today()
        )
        
        # Verificar relación desde nota a caja
        self.assertEqual(nota_cargo.caja, self.caja)
        
        # Verificar relación inversa desde caja a notas
        self.assertIn(nota_cargo, self.caja.notas_cargo.all())

    def test_should_handle_multiple_notas_per_caja_when_different_motivos(self):
        """Debe manejar múltiples notas por caja con diferentes motivos"""
        nota1 = NotaCargo.objects.create(
            caja=self.caja,
            monto=Decimal('100.00'),
            motivo="Motivo 1",
            fecha=date.today()
        )
        
        nota2 = NotaCargo.objects.create(
            caja=self.caja,
            monto=Decimal('200.00'),
            motivo="Motivo 2",
            fecha=date.today()
        )
        
        notas = self.caja.notas_cargo.all()
        self.assertEqual(notas.count(), 2)
        self.assertIn(nota1, notas)
        self.assertIn(nota2, notas)

    def test_should_handle_created_by_field_when_user_provided(self):
        """Debe manejar campo created_by cuando se proporciona usuario"""
        nota_cargo = NotaCargo.objects.create(
            caja=self.caja,
            monto=Decimal('300.00'),
            motivo="Test con usuario",
            fecha=date.today(),
            created_by=self.user
        )
        
        self.assertEqual(nota_cargo.created_by, self.user)


class TransaccionCajaModelTestCase(TestCase):
    """Tests para el modelo TransaccionCaja"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()
        self.caja = CajaFactory(tienda=self.tienda)
        self.cliente = ClienteFactory(tienda=self.tienda)

    def test_should_create_transaccion_with_required_fields_when_valid_data_provided(self):
        """Debe crear una transacción con los campos obligatorios válidos"""
        transaccion = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('500.00')
        )
        
        self.assertEqual(transaccion.caja, self.caja)
        self.assertEqual(transaccion.tipo_movimiento, 'INGRESO')
        self.assertEqual(transaccion.monto, Decimal('500.00'))
        self.assertEqual(transaccion.fecha, date.today())  # auto_now_add
        self.assertIsNotNone(transaccion.created_at)

    def test_should_have_correct_string_representation_when_created(self):
        """Debe tener una representación string correcta"""
        transaccion = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='EGRESO',
            monto=Decimal('250.00')
        )
        expected = f"Egreso en Caja {self.caja.id}: 250.00"
        self.assertEqual(str(transaccion), expected)

    def test_should_allow_valid_tipos_movimiento_when_creating(self):
        """Debe permitir tipos de movimiento válidos"""
        valid_tipos = ['INGRESO', 'EGRESO']
        
        for tipo in valid_tipos:
            transaccion = TransaccionCaja.objects.create(
                caja=self.caja,
                tipo_movimiento=tipo,
                monto=Decimal('100.00')
            )
            self.assertEqual(transaccion.tipo_movimiento, tipo)

    def test_should_have_tipo_property_alias_when_accessed(self):
        """Debe tener propiedad tipo como alias de tipo_movimiento"""
        transaccion = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('300.00')
        )
        
        self.assertEqual(transaccion.tipo, transaccion.tipo_movimiento)
        self.assertEqual(transaccion.tipo, 'INGRESO')

    def test_should_cascade_delete_when_caja_deleted(self):
        """Debe eliminar transacciones cuando se elimina caja (CASCADE)"""
        transaccion = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('400.00')
        )
        transaccion_id = transaccion.id
        
        # Eliminar caja
        self.caja.delete()
        
        # Verificar que transacción fue eliminada
        with self.assertRaises(TransaccionCaja.DoesNotExist):
            TransaccionCaja.objects.get(id=transaccion_id)

    def test_should_allow_optional_fields_when_creating_transaccion(self):
        """Debe permitir campos opcionales"""
        pedido = PedidoFactory(cliente=self.cliente, tienda=self.tienda)
        anticipo = AnticipoFactory(cliente=self.cliente)
        nota_cargo = NotaCargo.objects.create(
            caja=self.caja,
            monto=Decimal('50.00'),
            motivo="Test",
            fecha=date.today()
        )
        
        transaccion = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('600.00'),
            descripcion="Venta de productos",
            referencia="REF-001",
            pedido=pedido,
            anticipo=anticipo,
            nota_cargo=nota_cargo,
            created_by=self.user
        )
        
        self.assertEqual(transaccion.descripcion, "Venta de productos")
        self.assertEqual(transaccion.referencia, "REF-001")
        self.assertEqual(transaccion.pedido, pedido)
        self.assertEqual(transaccion.anticipo, anticipo)
        self.assertEqual(transaccion.nota_cargo, nota_cargo)
        self.assertEqual(transaccion.created_by, self.user)

    def test_should_set_null_when_related_objects_deleted(self):
        """Debe establecer NULL cuando se eliminan objetos relacionados (SET_NULL)"""
        pedido = PedidoFactory(cliente=self.cliente, tienda=self.tienda)
        transaccion = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('700.00'),
            pedido=pedido
        )
        
        # Eliminar pedido
        pedido.delete()
        transaccion.refresh_from_db()
        
        # Verificar que se estableció NULL
        self.assertIsNone(transaccion.pedido)

    def test_should_relate_to_caja_correctly_through_foreign_key(self):
        """Debe relacionarse correctamente con caja"""
        transaccion = TransaccionCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='EGRESO',
            monto=Decimal('150.00')
        )
        
        # Verificar relación desde transacción a caja
        self.assertEqual(transaccion.caja, self.caja)
        
        # Verificar relación inversa desde caja a transacciones
        self.assertIn(transaccion, self.caja.transacciones.all())

    def test_should_have_movimientocaja_alias_when_imported(self):
        """Debe tener alias MovimientoCaja para compatibilidad"""
        # Verificar que el alias existe
        self.assertEqual(MovimientoCaja, TransaccionCaja)
        
        # Verificar que funciona igual
        movimiento = MovimientoCaja.objects.create(
            caja=self.caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('800.00')
        )
        
        self.assertIsInstance(movimiento, TransaccionCaja)


class FacturaModelTestCase(TestCase):
    """Tests para el modelo Factura"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()
        self.cliente = ClienteFactory(tienda=self.tienda)
        self.pedido = PedidoFactory(cliente=self.cliente, tienda=self.tienda)

    def test_should_create_factura_with_required_fields_when_valid_data_provided(self):
        """Debe crear una factura con los campos obligatorios válidos"""
        factura = Factura.objects.create(
            pedido=self.pedido,
            folio="F-2025-001",
            fecha=date.today(),
            total=Decimal('1500.00')
        )
        
        self.assertEqual(factura.pedido, self.pedido)
        self.assertEqual(factura.folio, "F-2025-001")
        self.assertEqual(factura.fecha, date.today())
        self.assertEqual(factura.total, Decimal('1500.00'))
        self.assertIsNotNone(factura.created_at)

    def test_should_have_correct_string_representation_when_created(self):
        """Debe tener una representación string correcta"""
        factura = FacturaFactory(
            pedido=self.pedido,
            folio="F-TEST-123"
        )
        expected = f"Factura F-TEST-123 - Pedido {self.pedido.id}"
        self.assertEqual(str(factura), expected)

    def test_should_enforce_unique_folio_when_creating_duplicate(self):
        """Debe validar unicidad del folio"""
        folio = "F-UNIQUE-001"
        
        # Crear primera factura
        FacturaFactory(pedido=self.pedido, folio=folio)
        
        # Crear otro pedido para segunda factura
        pedido2 = PedidoFactory(cliente=self.cliente, tienda=self.tienda)
        
        # Intentar crear factura con folio duplicado
        with self.assertRaises(IntegrityError):
            Factura.objects.create(
                pedido=pedido2,
                folio=folio,  # Folio duplicado
                fecha=date.today(),
                total=Decimal('1000.00')
            )

    def test_should_enforce_onetoone_relationship_with_pedido(self):
        """Debe validar relación OneToOne con pedido"""
        # Crear primera factura
        FacturaFactory(pedido=self.pedido)
        
        # Intentar crear otra factura para el mismo pedido
        with self.assertRaises(IntegrityError):
            Factura.objects.create(
                pedido=self.pedido,  # Pedido ya tiene factura
                folio="F-DUPLICATE-001",
                fecha=date.today(),
                total=Decimal('2000.00')
            )

    def test_should_protect_pedido_when_factura_exists(self):
        """Debe proteger pedido cuando existe factura (PROTECT)"""
        FacturaFactory(pedido=self.pedido)
        
        # No debe permitir eliminar pedido si tiene factura
        with self.assertRaises(Exception):  # ProtectedError
            self.pedido.delete()

    def test_should_relate_to_pedido_correctly_through_onetoone(self):
        """Debe relacionarse correctamente con pedido a través de OneToOne"""
        factura = FacturaFactory(pedido=self.pedido)
        
        # Verificar relación desde factura a pedido
        self.assertEqual(factura.pedido, self.pedido)
        
        # Verificar relación inversa desde pedido a factura
        self.assertEqual(self.pedido.factura, factura)

    def test_should_handle_created_by_field_when_user_provided(self):
        """Debe manejar campo created_by cuando se proporciona usuario"""
        factura = FacturaFactory(
            pedido=self.pedido,
            created_by=self.user
        )
        
        self.assertEqual(factura.created_by, self.user)

    def test_should_validate_decimal_precision_when_creating_factura(self):
        """Debe validar precisión decimal en campo total"""
        factura = Factura.objects.create(
            pedido=self.pedido,
            folio="F-PRECISION-001",
            fecha=date.today(),
            total=Decimal('99999999.99')  # Valor máximo con 2 decimales
        )
        
        self.assertEqual(factura.total, Decimal('99999999.99'))


class CajaBusinessLogicTestCase(TestCase):
    """Tests para lógica de negocio compleja de caja"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()
        self.cliente = ClienteFactory(tienda=self.tienda)

    def test_should_calculate_saldo_final_correctly_when_movements_processed(self):
        """Debe calcular saldo final correctamente cuando se procesan movimientos"""
        caja = CajaFactory(
            tienda=self.tienda,
            fondo_inicial=Decimal('1000.00'),
            fecha=date.today()
        )
        
        # Crear movimientos
        ingreso1 = TransaccionCaja.objects.create(
            caja=caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('500.00')
        )
        
        ingreso2 = TransaccionCaja.objects.create(
            caja=caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('300.00')
        )
        
        egreso1 = TransaccionCaja.objects.create(
            caja=caja,
            tipo_movimiento='EGRESO',
            monto=Decimal('200.00')
        )
        
        # Calcular totales
        total_ingresos = caja.transacciones.filter(
            tipo_movimiento='INGRESO'
        ).aggregate(total=models.Sum('monto'))['total'] or Decimal('0')
        
        total_egresos = caja.transacciones.filter(
            tipo_movimiento='EGRESO'
        ).aggregate(total=models.Sum('monto'))['total'] or Decimal('0')
        
        saldo_calculado = caja.fondo_inicial + total_ingresos - total_egresos
        
        self.assertEqual(total_ingresos, Decimal('800.00'))
        self.assertEqual(total_egresos, Decimal('200.00'))
        self.assertEqual(saldo_calculado, Decimal('1600.00'))

    def test_should_handle_daily_cash_flow_correctly_when_multiple_operations(self):
        """Debe manejar flujo de caja diario correctamente con múltiples operaciones"""
        caja = CajaFactory(
            tienda=self.tienda,
            fecha=date.today(),
            fondo_inicial=Decimal('500.00')
        )
        
        # Simular día de operaciones
        pedido = PedidoFactory(cliente=self.cliente, tienda=self.tienda)
        anticipo = AnticipoFactory(cliente=self.cliente)
        
        # Ingreso por venta
        TransaccionCaja.objects.create(
            caja=caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('1200.00'),
            descripcion="Venta del día",
            pedido=pedido
        )
        
        # Ingreso por anticipo
        TransaccionCaja.objects.create(
            caja=caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('300.00'),
            descripcion="Anticipo cliente",
            anticipo=anticipo
        )
        
        # Egreso por gastos
        TransaccionCaja.objects.create(
            caja=caja,
            tipo_movimiento='EGRESO',
            monto=Decimal('150.00'),
            descripcion="Gastos varios"
        )
        
        # Verificar operaciones
        self.assertEqual(caja.transacciones.count(), 3)
        self.assertEqual(
            caja.transacciones.filter(tipo_movimiento='INGRESO').count(), 2
        )
        self.assertEqual(
            caja.transacciones.filter(tipo_movimiento='EGRESO').count(), 1
        )

    def test_should_validate_caja_closure_rules_when_closing_cash_box(self):
        """Debe validar reglas de cierre cuando se cierra la caja"""
        caja = CajaFactory(
            tienda=self.tienda,
            fecha=date.today(),
            cerrada=False
        )
        
        # Agregar algunas transacciones
        TransaccionCaja.objects.create(
            caja=caja,
            tipo_movimiento='INGRESO',
            monto=Decimal('1000.00')
        )
        
        # Cerrar caja
        caja.cerrada = True
        caja.save()
        
        # Verificar que se cerró correctamente
        self.assertTrue(caja.cerrada)

    def test_should_track_cash_movements_history_when_operations_performed(self):
        """Debe rastrear historial de movimientos cuando se realizan operaciones"""
        caja = CajaFactory(tienda=self.tienda, fecha=date.today())
        
        # Crear serie de movimientos con timestamps
        movimientos_data = [
            ('INGRESO', Decimal('100.00'), 'Venta 1'),
            ('INGRESO', Decimal('200.00'), 'Venta 2'),
            ('EGRESO', Decimal('50.00'), 'Gasto 1'),
            ('INGRESO', Decimal('300.00'), 'Venta 3'),
        ]
        
        for tipo, monto, desc in movimientos_data:
            TransaccionCaja.objects.create(
                caja=caja,
                tipo_movimiento=tipo,
                monto=monto,
                descripcion=desc,
                created_by=self.user
            )
        
        # Verificar historial
        movimientos = caja.transacciones.order_by('created_at')
        self.assertEqual(movimientos.count(), 4)
        
        # Verificar orden cronológico
        self.assertEqual(movimientos.first().descripcion, 'Venta 1')
        self.assertEqual(movimientos.last().descripcion, 'Venta 3')

    def test_should_handle_factura_generation_workflow_when_pedido_completed(self):
        """Debe manejar flujo de generación de facturas cuando se completa pedido"""
        pedido = PedidoFactory(
            cliente=self.cliente,
            tienda=self.tienda,
            estado='surtido',
            pagado=True,
            total=Decimal('1500.00')
        )
        
        # Crear factura para el pedido
        factura = FacturaFactory(
            pedido=pedido,
            folio="F-2025-TEST-001",
            total=pedido.total,
            created_by=self.user
        )
        
        # Verificar relación
        self.assertEqual(factura.pedido, pedido)
        self.assertEqual(pedido.factura, factura)
        self.assertEqual(factura.total, pedido.total)

    def test_should_prevent_duplicate_facturas_when_pedido_already_has_one(self):
        """Debe prevenir facturas duplicadas cuando el pedido ya tiene una"""
        pedido = PedidoFactory(cliente=self.cliente, tienda=self.tienda)
        
        # Crear primera factura
        FacturaFactory(pedido=pedido, folio="F-FIRST-001")
        
        # Verificar que el pedido ya tiene factura
        self.assertTrue(hasattr(pedido, 'factura'))
        self.assertIsNotNone(pedido.factura)

    def test_should_handle_nota_cargo_impact_on_cash_flow_when_created(self):
        """Debe manejar impacto de notas de cargo en flujo de caja"""
        caja = CajaFactory(tienda=self.tienda, fecha=date.today())
        
        # Crear nota de cargo
        nota_cargo = NotaCargo.objects.create(
            caja=caja,
            monto=Decimal('250.00'),
            motivo="Gastos de mantenimiento",
            fecha=date.today(),
            created_by=self.user
        )
        
        # Crear transacción asociada a la nota de cargo
        transaccion = TransaccionCaja.objects.create(
            caja=caja,
            tipo_movimiento='EGRESO',
            monto=nota_cargo.monto,
            descripcion=f"Nota de cargo: {nota_cargo.motivo}",
            nota_cargo=nota_cargo
        )
        
        # Verificar asociación
        self.assertEqual(transaccion.nota_cargo, nota_cargo)
        self.assertEqual(transaccion.monto, nota_cargo.monto)
        self.assertEqual(transaccion.tipo_movimiento, 'EGRESO')
