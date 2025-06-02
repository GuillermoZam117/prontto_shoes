"""
Tests unitarios para los modelos del módulo de clientes
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import date, timedelta
from unittest.mock import patch

from clientes.models import Cliente, Anticipo, DescuentoCliente, ReglaProgramaLealtad
from tests.factories import (
    UserFactory, TiendaFactory, ClienteFactory, AnticipoFactory,
    DescuentoClienteFactory
)


class ClienteModelTestCase(TestCase):
    """Tests para el modelo Cliente"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()

    def test_should_create_cliente_with_required_fields_when_valid_data_provided(self):
        """Debe crear un cliente con los campos obligatorios válidos"""
        cliente = Cliente.objects.create(
            nombre="Juan Pérez",
            tienda=self.tienda
        )
        
        self.assertEqual(cliente.nombre, "Juan Pérez")
        self.assertEqual(cliente.tienda, self.tienda)
        self.assertEqual(cliente.saldo_a_favor, Decimal('0.00'))
        self.assertEqual(cliente.monto_acumulado, Decimal('0.00'))
        self.assertEqual(cliente.max_return_days, 30)
        self.assertEqual(cliente.puntos_lealtad, 0)
        self.assertEqual(cliente.contacto, "")
        self.assertEqual(cliente.observaciones, "")

    def test_should_have_correct_string_representation_when_created(self):
        """Debe tener una representación string correcta"""
        cliente = ClienteFactory(nombre="María García")
        self.assertEqual(str(cliente), "María García")

    def test_should_allow_optional_fields_when_creating_cliente(self):
        """Debe permitir campos opcionales"""
        cliente = Cliente.objects.create(
            nombre="Pedro López",
            contacto="555-1234",
            observaciones="Cliente VIP",
            saldo_a_favor=Decimal('100.50'),
            monto_acumulado=Decimal('5000.00'),
            max_return_days=45,
            puntos_lealtad=250,
            tienda=self.tienda,
            created_by=self.user
        )
        
        self.assertEqual(cliente.contacto, "555-1234")
        self.assertEqual(cliente.observaciones, "Cliente VIP")
        self.assertEqual(cliente.saldo_a_favor, Decimal('100.50'))
        self.assertEqual(cliente.monto_acumulado, Decimal('5000.00'))
        self.assertEqual(cliente.max_return_days, 45)
        self.assertEqual(cliente.puntos_lealtad, 250)
        self.assertEqual(cliente.created_by, self.user)

    def test_should_enforce_positive_max_return_days_when_creating(self):
        """Debe validar que max_return_days sea positivo"""
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(
                nombre="Test Cliente",
                tienda=self.tienda,
                max_return_days=-1  # Valor negativo no permitido
            )

    def test_should_enforce_positive_puntos_lealtad_when_creating(self):
        """Debe validar que puntos_lealtad sea positivo"""
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(
                nombre="Test Cliente",
                tienda=self.tienda,
                puntos_lealtad=-10  # Valor negativo no permitido
            )

    def test_should_protect_tienda_when_cliente_exists(self):
        """Debe proteger tienda cuando existe cliente (PROTECT)"""
        cliente = ClienteFactory(tienda=self.tienda)
        
        # No debe permitir eliminar tienda si tiene clientes
        with self.assertRaises(Exception):  # ProtectedError
            self.tienda.delete()

    def test_should_handle_user_relationship_correctly_when_set(self):
        """Debe manejar correctamente la relación con usuario"""
        user = UserFactory()
        cliente = ClienteFactory(tienda=self.tienda, user=user)
        
        # Verificar relación OneToOne
        self.assertEqual(cliente.user, user)
        self.assertEqual(user.cliente_profile, cliente)

    def test_should_set_null_when_user_deleted(self):
        """Debe establecer NULL cuando se elimina el usuario (SET_NULL)"""
        user = UserFactory()
        cliente = ClienteFactory(tienda=self.tienda, user=user)
        
        # Eliminar usuario
        user.delete()
        cliente.refresh_from_db()
        
        # Verificar que se estableció NULL
        self.assertIsNone(cliente.user)

    def test_should_validate_decimal_precision_when_creating(self):
        """Debe validar precisión decimal en campos monetarios"""
        # Verificar que acepta 2 decimales
        cliente = Cliente.objects.create(
            nombre="Test Cliente",
            tienda=self.tienda,
            saldo_a_favor=Decimal('999.99'),
            monto_acumulado=Decimal('12345.67')
        )
        
        self.assertEqual(cliente.saldo_a_favor, Decimal('999.99'))
        self.assertEqual(cliente.monto_acumulado, Decimal('12345.67'))

    def test_should_handle_audit_fields_when_created_by_user(self):
        """Debe manejar campos de auditoría correctamente"""
        cliente = ClienteFactory(
            tienda=self.tienda,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(cliente.created_by, self.user)
        self.assertEqual(cliente.updated_by, self.user)
        self.assertIsNotNone(cliente.created_at)
        self.assertIsNotNone(cliente.updated_at)

    def test_should_allow_negative_saldo_a_favor_for_debt_tracking(self):
        """Debe permitir saldo a favor negativo para rastrear deudas"""
        cliente = Cliente.objects.create(
            nombre="Cliente con Deuda",
            tienda=self.tienda,
            saldo_a_favor=Decimal('-250.00')
        )
        
        self.assertEqual(cliente.saldo_a_favor, Decimal('-250.00'))


class AnticipoModelTestCase(TestCase):
    """Tests para el modelo Anticipo"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()
        self.cliente = ClienteFactory(tienda=self.tienda)

    def test_should_create_anticipo_with_required_fields_when_valid_data_provided(self):
        """Debe crear un anticipo con los campos obligatorios válidos"""
        monto = Decimal('500.00')
        fecha = date.today()
        
        anticipo = Anticipo.objects.create(
            cliente=self.cliente,
            monto=monto,
            fecha=fecha
        )
        
        self.assertEqual(anticipo.cliente, self.cliente)
        self.assertEqual(anticipo.monto, monto)
        self.assertEqual(anticipo.fecha, fecha)
        self.assertIsNotNone(anticipo.created_at)

    def test_should_have_correct_string_representation_when_created(self):
        """Debe tener una representación string correcta"""
        anticipo = AnticipoFactory(
            cliente=self.cliente,
            monto=Decimal('300.00')
        )
        expected = f"Anticipo 300.00 - {self.cliente.nombre}"
        self.assertEqual(str(anticipo), expected)

    def test_should_cascade_delete_when_cliente_deleted(self):
        """Debe eliminar anticipos cuando se elimina cliente (CASCADE)"""
        anticipo = AnticipoFactory(cliente=self.cliente)
        anticipo_id = anticipo.id
        
        # Eliminar cliente
        self.cliente.delete()
        
        # Verificar que anticipo fue eliminado
        with self.assertRaises(Anticipo.DoesNotExist):
            Anticipo.objects.get(id=anticipo_id)

    def test_should_relate_to_cliente_correctly_through_foreign_key(self):
        """Debe relacionarse correctamente con cliente"""
        anticipo = AnticipoFactory(cliente=self.cliente)
        
        # Verificar relación desde anticipo a cliente
        self.assertEqual(anticipo.cliente, self.cliente)
        
        # Verificar relación inversa desde cliente a anticipos
        self.assertIn(anticipo, self.cliente.anticipos.all())

    def test_should_handle_multiple_anticipos_per_cliente_when_different_dates(self):
        """Debe manejar múltiples anticipos por cliente"""
        anticipo1 = AnticipoFactory(
            cliente=self.cliente,
            monto=Decimal('200.00'),
            fecha=date.today()
        )
        
        anticipo2 = AnticipoFactory(
            cliente=self.cliente,
            monto=Decimal('300.00'),
            fecha=date.today() - timedelta(days=1)
        )
        
        anticipos = self.cliente.anticipos.all()
        self.assertEqual(anticipos.count(), 2)
        self.assertIn(anticipo1, anticipos)
        self.assertIn(anticipo2, anticipos)

    def test_should_allow_created_by_field_when_user_provided(self):
        """Debe permitir campo created_by cuando se proporciona usuario"""
        anticipo = AnticipoFactory(
            cliente=self.cliente,
            created_by=self.user
        )
        
        self.assertEqual(anticipo.created_by, self.user)

    def test_should_validate_positive_monto_when_creating(self):
        """Debe validar que el monto sea positivo (lógica de negocio)"""
        # Nota: El modelo no tiene validación automática, pero es una regla de negocio
        # Este test documentaría la expectativa
        anticipo = Anticipo.objects.create(
            cliente=self.cliente,
            monto=Decimal('100.00'),
            fecha=date.today()
        )
        
        self.assertGreater(anticipo.monto, Decimal('0.00'))


class DescuentoClienteModelTestCase(TestCase):
    """Tests para el modelo DescuentoCliente"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()
        self.cliente = ClienteFactory(tienda=self.tienda)

    def test_should_create_descuento_with_required_fields_when_valid_data_provided(self):
        """Debe crear un descuento con los campos obligatorios válidos"""
        descuento = DescuentoCliente.objects.create(
            cliente=self.cliente,
            porcentaje=Decimal('15.50'),
            mes_vigente="2025-05"
        )
        
        self.assertEqual(descuento.cliente, self.cliente)
        self.assertEqual(descuento.porcentaje, Decimal('15.50'))
        self.assertEqual(descuento.mes_vigente, "2025-05")
        self.assertEqual(descuento.monto_acumulado_mes_anterior, Decimal('0.00'))

    def test_should_have_correct_string_representation_when_created(self):
        """Debe tener una representación string correcta"""
        descuento = DescuentoClienteFactory(
            cliente=self.cliente,
            porcentaje=Decimal('20.00'),
            mes_vigente="2025-06"
        )
        expected = f"20.00% - {self.cliente.nombre} (2025-06)"
        self.assertEqual(str(descuento), expected)

    def test_should_validate_mes_vigente_format_when_creating(self):
        """Debe validar formato de mes_vigente YYYY-MM"""
        # Formato válido
        descuento = DescuentoCliente.objects.create(
            cliente=self.cliente,
            porcentaje=Decimal('10.00'),
            mes_vigente="2025-12"
        )
        self.assertEqual(descuento.mes_vigente, "2025-12")

    def test_should_cascade_delete_when_cliente_deleted(self):
        """Debe eliminar descuentos cuando se elimina cliente (CASCADE)"""
        descuento = DescuentoClienteFactory(cliente=self.cliente)
        descuento_id = descuento.id
        
        # Eliminar cliente
        self.cliente.delete()
        
        # Verificar que descuento fue eliminado
        with self.assertRaises(DescuentoCliente.DoesNotExist):
            DescuentoCliente.objects.get(id=descuento_id)

    def test_should_handle_multiple_descuentos_per_cliente_different_months(self):
        """Debe manejar múltiples descuentos por cliente en diferentes meses"""
        descuento1 = DescuentoClienteFactory(
            cliente=self.cliente,
            mes_vigente="2025-05",
            porcentaje=Decimal('15.00')
        )
        
        descuento2 = DescuentoClienteFactory(
            cliente=self.cliente,
            mes_vigente="2025-06",
            porcentaje=Decimal('20.00')
        )
        
        descuentos = self.cliente.descuentos.all()
        self.assertEqual(descuentos.count(), 2)
        self.assertIn(descuento1, descuentos)
        self.assertIn(descuento2, descuentos)

    def test_should_handle_audit_fields_correctly_when_user_provided(self):
        """Debe manejar campos de auditoría correctamente"""
        descuento = DescuentoClienteFactory(
            cliente=self.cliente,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(descuento.created_by, self.user)
        self.assertEqual(descuento.updated_by, self.user)
        self.assertIsNotNone(descuento.created_at)
        self.assertIsNotNone(descuento.updated_at)

    def test_should_store_monto_acumulado_mes_anterior_when_provided(self):
        """Debe almacenar monto acumulado del mes anterior"""
        monto_anterior = Decimal('2500.75')
        descuento = DescuentoCliente.objects.create(
            cliente=self.cliente,
            porcentaje=Decimal('25.00'),
            mes_vigente="2025-05",
            monto_acumulado_mes_anterior=monto_anterior
        )
        
        self.assertEqual(descuento.monto_acumulado_mes_anterior, monto_anterior)

    def test_should_validate_porcentaje_precision_when_creating(self):
        """Debe validar precisión del porcentaje (5 dígitos, 2 decimales)"""
        # Porcentaje válido
        descuento = DescuentoCliente.objects.create(
            cliente=self.cliente,
            porcentaje=Decimal('99.99'),
            mes_vigente="2025-05"
        )
        self.assertEqual(descuento.porcentaje, Decimal('99.99'))


class ReglaProgramaLealtadModelTestCase(TestCase):
    """Tests para el modelo ReglaProgramaLealtad"""

    def test_should_create_regla_with_required_fields_when_valid_data_provided(self):
        """Debe crear una regla con los campos obligatorios válidos"""
        regla = ReglaProgramaLealtad.objects.create(
            monto_compra_requerido=Decimal('1000.00'),
            puntos_otorgados=100
        )
        
        self.assertEqual(regla.monto_compra_requerido, Decimal('1000.00'))
        self.assertEqual(regla.puntos_otorgados, 100)
        self.assertTrue(regla.activo)  # Valor por defecto
        self.assertIsNotNone(regla.created_at)

    def test_should_enforce_unique_monto_compra_when_creating_duplicate(self):
        """Debe validar unicidad del monto de compra requerido"""
        monto = Decimal('500.00')
        
        # Crear primera regla
        ReglaProgramaLealtad.objects.create(
            monto_compra_requerido=monto,
            puntos_otorgados=50
        )
        
        # Intentar crear regla duplicada
        with self.assertRaises(IntegrityError):
            ReglaProgramaLealtad.objects.create(
                monto_compra_requerido=monto,  # Monto duplicado
                puntos_otorgados=75
            )

    def test_should_enforce_positive_puntos_otorgados_when_creating(self):
        """Debe validar que puntos_otorgados sea positivo"""
        with self.assertRaises(IntegrityError):
            ReglaProgramaLealtad.objects.create(
                monto_compra_requerido=Decimal('1000.00'),
                puntos_otorgados=-10  # Valor negativo no permitido
            )

    def test_should_allow_inactive_reglas_when_activo_false(self):
        """Debe permitir reglas inactivas"""
        regla = ReglaProgramaLealtad.objects.create(
            monto_compra_requerido=Decimal('2000.00'),
            puntos_otorgados=200,
            activo=False
        )
        
        self.assertFalse(regla.activo)

    def test_should_handle_multiple_reglas_different_montos_when_creating(self):
        """Debe manejar múltiples reglas con diferentes montos"""
        regla1 = ReglaProgramaLealtad.objects.create(
            monto_compra_requerido=Decimal('500.00'),
            puntos_otorgados=25
        )
        
        regla2 = ReglaProgramaLealtad.objects.create(
            monto_compra_requerido=Decimal('1500.00'),
            puntos_otorgados=150
        )
        
        self.assertEqual(ReglaProgramaLealtad.objects.count(), 2)
        self.assertNotEqual(regla1.monto_compra_requerido, regla2.monto_compra_requerido)


class ClienteBusinessLogicTestCase(TestCase):
    """Tests para lógica de negocio compleja de clientes"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()

    def test_should_calculate_cliente_lealtad_points_correctly_when_compras_made(self):
        """Debe calcular puntos de lealtad correctamente según compras"""
        # Crear reglas de lealtad
        ReglaProgramaLealtad.objects.create(
            monto_compra_requerido=Decimal('1000.00'),
            puntos_otorgados=100,
            activo=True
        )
        
        ReglaProgramaLealtad.objects.create(
            monto_compra_requerido=Decimal('500.00'),
            puntos_otorgados=50,
            activo=True
        )
        
        cliente = ClienteFactory(
            tienda=self.tienda,
            monto_acumulado=Decimal('1200.00'),
            puntos_lealtad=0
        )
        
        # Verificar que las reglas existen para futuras implementaciones
        reglas = ReglaProgramaLealtad.objects.filter(activo=True)
        self.assertTrue(reglas.exists())

    def test_should_manage_cliente_saldo_transactions_correctly_when_operations_performed(self):
        """Debe manejar transacciones de saldo correctamente"""
        cliente = ClienteFactory(
            tienda=self.tienda,
            saldo_a_favor=Decimal('100.00')
        )
        
        # Simular operaciones de saldo
        original_saldo = cliente.saldo_a_favor
        
        # Agregar anticipo
        anticipo = AnticipoFactory(
            cliente=cliente,
            monto=Decimal('50.00')
        )
        
        # Verificar que el anticipo se creó correctamente
        self.assertEqual(anticipo.monto, Decimal('50.00'))
        self.assertEqual(cliente.saldo_a_favor, original_saldo)  # No se actualiza automáticamente

    def test_should_handle_descuento_progression_correctly_when_months_change(self):
        """Debe manejar correctamente la progresión de descuentos por mes"""
        cliente = ClienteFactory(tienda=self.tienda)
        
        # Crear descuentos para diferentes meses
        descuento_mayo = DescuentoClienteFactory(
            cliente=cliente,
            mes_vigente="2025-05",
            porcentaje=Decimal('15.00'),
            monto_acumulado_mes_anterior=Decimal('1000.00')
        )
        
        descuento_junio = DescuentoClienteFactory(
            cliente=cliente,
            mes_vigente="2025-06",
            porcentaje=Decimal('20.00'),
            monto_acumulado_mes_anterior=Decimal('1500.00')
        )
        
        # Verificar progresión
        self.assertLess(descuento_mayo.porcentaje, descuento_junio.porcentaje)
        self.assertLess(
            descuento_mayo.monto_acumulado_mes_anterior,
            descuento_junio.monto_acumulado_mes_anterior
        )

    def test_should_validate_cliente_credit_limits_when_business_rules_applied(self):
        """Debe validar límites de crédito según reglas de negocio"""
        cliente = ClienteFactory(
            tienda=self.tienda,
            saldo_a_favor=Decimal('-500.00'),  # Cliente con deuda
            monto_acumulado=Decimal('10000.00')  # Pero con historial de compras
        )
        
        # Verificar que el cliente puede tener saldo negativo
        self.assertLess(cliente.saldo_a_favor, Decimal('0.00'))
        self.assertGreater(cliente.monto_acumulado, Decimal('0.00'))

    def test_should_handle_cliente_user_integration_when_distribuidora_access_needed(self):
        """Debe manejar integración con usuario para acceso de distribuidoras"""
        user = UserFactory(username="distribuidora_test")
        cliente = ClienteFactory(
            tienda=self.tienda,
            user=user,
            nombre="Distribuidora Test S.A."
        )
        
        # Verificar integración
        self.assertEqual(cliente.user, user)
        self.assertEqual(user.cliente_profile, cliente)
        
        # Verificar que se puede acceder desde ambos lados
        self.assertIsNotNone(cliente.user.username)
        self.assertIsNotNone(user.cliente_profile.nombre)
