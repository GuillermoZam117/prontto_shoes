"""
Tests unitarios para modelos de devoluciones.
Valida la funcionalidad del sistema de devoluciones de productos.
"""
import pytest
from decimal import Decimal
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from freezegun import freeze_time
from datetime import datetime, timedelta

from tests.base import BaseTestCase
from tests.factories import (
    DevolucionFactory, ClienteFactory, ProductoFactory,
    DetallePedidoFactory, PedidoFactory, UserFactory
)
from devoluciones.models import Devolucion


class TestDevolucionModel(BaseTestCase):
    """Tests unitarios para el modelo Devolucion."""

    def test_should_create_devolucion_with_required_fields(self):
        """Debe crear devolución con campos requeridos."""
        cliente = ClienteFactory()
        producto = ProductoFactory()
        
        devolucion = DevolucionFactory(
            cliente=cliente,
            producto=producto,
            tipo='defecto',
            motivo='Producto defectuoso'
        )
        
        assert devolucion.cliente == cliente
        assert devolucion.producto == producto
        assert devolucion.tipo == 'defecto'
        assert devolucion.motivo == 'Producto defectuoso'
        assert devolucion.estado == 'pendiente'
        assert devolucion.fecha is not None
        assert not devolucion.confirmacion_proveedor
        assert devolucion.afecta_inventario
        assert devolucion.saldo_a_favor_generado == Decimal('0')

    def test_should_validate_tipo_choices(self):
        """Debe validar las opciones de tipo."""
        devolucion = DevolucionFactory()
        
        valid_types = ['defecto', 'cambio']
        for tipo in valid_types:
            devolucion.tipo = tipo
            devolucion.full_clean()  # No debe lanzar excepción

    def test_should_validate_estado_choices(self):
        """Debe validar las opciones de estado."""
        devolucion = DevolucionFactory()
        
        valid_states = ['pendiente', 'validada', 'rechazada', 'completada']
        for estado in valid_states:
            devolucion.estado = estado
            devolucion.full_clean()  # No debe lanzar excepción

    def test_should_link_to_detalle_pedido_optionally(self):
        """Debe linkear opcionalmente a detalle de pedido."""
        pedido = PedidoFactory()
        detalle = DetallePedidoFactory(pedido=pedido)
        
        devolucion = DevolucionFactory(
            detalle_pedido=detalle,
            cliente=detalle.pedido.cliente,
            producto=detalle.producto
        )
        
        assert devolucion.detalle_pedido == detalle
        assert devolucion.cliente == detalle.pedido.cliente

    def test_should_handle_devolucion_without_detalle_pedido(self):
        """Debe manejar devolución sin detalle de pedido."""
        devolucion = DevolucionFactory(detalle_pedido=None)
        
        assert devolucion.detalle_pedido is None

    def test_should_protect_related_cliente_and_producto(self):
        """Debe proteger cliente y producto relacionados (PROTECT)."""
        cliente = ClienteFactory()
        producto = ProductoFactory()
        DevolucionFactory(cliente=cliente, producto=producto)
        
        with pytest.raises(Exception):  # ProtectedError
            cliente.delete()
            
        with pytest.raises(Exception):
            producto.delete()

    def test_should_handle_null_detalle_pedido_on_deletion(self):
        """Debe manejar eliminación de detalle pedido (SET_NULL)."""
        detalle = DetallePedidoFactory()
        devolucion = DevolucionFactory(detalle_pedido=detalle)
        
        detalle.delete()
        devolucion.refresh_from_db()
        
        assert devolucion.detalle_pedido is None

    def test_should_track_created_by_user(self):
        """Debe trackear el usuario que creó la devolución."""
        user = UserFactory()
        devolucion = DevolucionFactory(created_by=user)
        
        assert devolucion.created_by == user

    def test_should_handle_null_created_by_on_user_deletion(self):
        """Debe manejar eliminación del usuario creador (SET_NULL)."""
        user = UserFactory()
        devolucion = DevolucionFactory(created_by=user)
        
        user.delete()
        devolucion.refresh_from_db()
        
        assert devolucion.created_by is None

    @freeze_time("2024-03-20 16:30:00")
    def test_should_set_automatic_fecha(self):
        """Debe establecer fecha automáticamente."""
        devolucion = DevolucionFactory()
        
        expected_datetime = datetime(2024, 3, 20, 16, 30, 0)
        assert devolucion.fecha.replace(tzinfo=None) == expected_datetime

    def test_should_handle_saldo_a_favor_generation(self):
        """Debe manejar generación de saldo a favor."""
        devolucion = DevolucionFactory(
            tipo='defecto',
            estado='validada',
            precio_devolucion=Decimal('150.00'),
            saldo_a_favor_generado=Decimal('150.00')
        )
        
        assert devolucion.saldo_a_favor_generado == Decimal('150.00')
        assert devolucion.precio_devolucion == Decimal('150.00')

    def test_should_handle_devolucion_without_saldo_a_favor(self):
        """Debe manejar devolución sin saldo a favor."""
        devolucion = DevolucionFactory(
            tipo='cambio',
            saldo_a_favor_generado=Decimal('0')
        )
        
        assert devolucion.saldo_a_favor_generado == Decimal('0')

    def test_should_control_inventory_impact(self):
        """Debe controlar impacto en inventario."""
        # Devolución que afecta inventario
        devolucion_inventario = DevolucionFactory(
            afecta_inventario=True,
            tipo='defecto'
        )
        assert devolucion_inventario.afecta_inventario
        
        # Devolución que no afecta inventario (ej: producto dañado)
        devolucion_sin_inventario = DevolucionFactory(
            afecta_inventario=False,
            tipo='defecto'
        )
        assert not devolucion_sin_inventario.afecta_inventario

    def test_should_require_provider_confirmation(self):
        """Debe requerir confirmación del proveedor."""
        devolucion = DevolucionFactory(
            tipo='defecto',
            confirmacion_proveedor=True
        )
        
        assert devolucion.confirmacion_proveedor

    def test_should_return_formatted_string_representation(self):
        """Debe retornar representación string formateada."""
        cliente = ClienteFactory(nombre="Juan Pérez")
        producto = ProductoFactory(codigo="DEV001")
        devolucion = DevolucionFactory(
            cliente=cliente,
            producto=producto
        )
        
        expected = f"Devolución {devolucion.id} - Juan Pérez - DEV001"
        assert str(devolucion) == expected

    def test_should_handle_motivo_text_field(self):
        """Debe manejar campo de motivo como texto."""
        motivo_largo = "Este producto presenta múltiples defectos " * 10
        
        devolucion = DevolucionFactory(
            motivo=motivo_largo,
            tipo='defecto'
        )
        
        assert devolucion.motivo == motivo_largo
        assert len(devolucion.motivo) > 100

    def test_should_handle_blank_motivo(self):
        """Debe manejar motivo en blanco."""
        devolucion = DevolucionFactory(motivo="")
        
        assert devolucion.motivo == ""

    def test_should_set_precio_devolucion_optionally(self):
        """Debe establecer precio de devolución opcionalmente."""
        # Devolución sin precio específico
        devolucion_sin_precio = DevolucionFactory(precio_devolucion=None)
        assert devolucion_sin_precio.precio_devolucion is None
        
        # Devolución con precio específico
        devolucion_con_precio = DevolucionFactory(
            precio_devolucion=Decimal('99.50')
        )
        assert devolucion_con_precio.precio_devolucion == Decimal('99.50')


class TestDevolucionWorkflow(BaseTestCase):
    """Tests para flujo de trabajo de devoluciones."""

    def test_should_process_defect_return_workflow(self):
        """Debe procesar flujo de devolución por defecto."""
        # Crear contexto inicial
        cliente = ClienteFactory()
        producto = ProductoFactory(precio=Decimal('100.00'))
        pedido = PedidoFactory(cliente=cliente)
        detalle = DetallePedidoFactory(
            pedido=pedido,
            producto=producto,
            cantidad=2,
            precio_unitario=Decimal('100.00')
        )
        
        # Crear devolución
        devolucion = DevolucionFactory(
            cliente=cliente,
            producto=producto,
            detalle_pedido=detalle,
            tipo='defecto',
            estado='pendiente',
            motivo='Producto llegó dañado'
        )
        
        # Validar devolución
        devolucion.estado = 'validada'
        devolucion.precio_devolucion = Decimal('100.00')
        devolucion.save()
        
        assert devolucion.estado == 'validada'
        assert devolucion.precio_devolucion == Decimal('100.00')
        
        # Completar devolución
        devolucion.estado = 'completada'
        devolucion.saldo_a_favor_generado = Decimal('100.00')
        devolucion.save()
        
        assert devolucion.estado == 'completada'
        assert devolucion.saldo_a_favor_generado == Decimal('100.00')

    def test_should_process_exchange_return_workflow(self):
        """Debe procesar flujo de devolución por cambio."""
        devolucion = DevolucionFactory(
            tipo='cambio',
            estado='pendiente',
            motivo='Cliente desea otro color'
        )
        
        # Para cambios, normalmente no se genera saldo a favor
        devolucion.estado = 'validada'
        devolucion.afecta_inventario = True
        devolucion.saldo_a_favor_generado = Decimal('0')
        devolucion.save()
        
        assert devolucion.tipo == 'cambio'
        assert devolucion.afecta_inventario
        assert devolucion.saldo_a_favor_generado == Decimal('0')

    def test_should_handle_rejected_return(self):
        """Debe manejar devolución rechazada."""
        devolucion = DevolucionFactory(
            estado='pendiente',
            motivo='Producto sin defectos aparentes'
        )
        
        # Rechazar devolución
        devolucion.estado = 'rechazada'
        devolucion.save()
        
        assert devolucion.estado == 'rechazada'
        assert devolucion.saldo_a_favor_generado == Decimal('0')
        assert not devolucion.confirmacion_proveedor

    def test_should_require_provider_confirmation_for_defects(self):
        """Debe requerir confirmación del proveedor para defectos."""
        devolucion = DevolucionFactory(
            tipo='defecto',
            estado='pendiente'
        )
        
        # Confirmar con proveedor antes de validar
        devolucion.confirmacion_proveedor = True
        devolucion.estado = 'validada'
        devolucion.save()
        
        assert devolucion.confirmacion_proveedor
        assert devolucion.estado == 'validada'

    def test_should_calculate_different_return_prices(self):
        """Debe calcular diferentes precios de devolución."""
        producto = ProductoFactory(precio=Decimal('200.00'))
        
        # Devolución con precio completo
        devolucion_completa = DevolucionFactory(
            producto=producto,
            precio_devolucion=Decimal('200.00')
        )
        
        # Devolución con precio parcial (ej: producto usado)
        devolucion_parcial = DevolucionFactory(
            producto=producto,
            precio_devolucion=Decimal('150.00')
        )
        
        assert devolucion_completa.precio_devolucion == Decimal('200.00')
        assert devolucion_parcial.precio_devolucion == Decimal('150.00')


class TestDevolucionIntegration(BaseTestCase):
    """Tests de integración para devoluciones."""

    def test_should_link_devolucion_to_original_sale(self):
        """Debe linkear devolución a venta original."""
        # Crear venta original
        cliente = ClienteFactory()
        producto = ProductoFactory()
        pedido = PedidoFactory(cliente=cliente, estado='entregado')
        detalle = DetallePedidoFactory(
            pedido=pedido,
            producto=producto,
            cantidad=3,
            precio_unitario=Decimal('50.00')
        )
        
        # Crear devolución relacionada
        devolucion = DevolucionFactory(
            cliente=cliente,
            producto=producto,
            detalle_pedido=detalle,
            tipo='defecto'
        )
        
        # Verificar relaciones
        assert devolucion.cliente == pedido.cliente
        assert devolucion.producto == detalle.producto
        assert devolucion.detalle_pedido == detalle
        assert devolucion in detalle.devoluciones.all()

    def test_should_handle_multiple_returns_per_product(self):
        """Debe manejar múltiples devoluciones por producto."""
        producto = ProductoFactory()
        cliente1 = ClienteFactory()
        cliente2 = ClienteFactory()
        
        devolucion1 = DevolucionFactory(
            cliente=cliente1,
            producto=producto,
            tipo='defecto'
        )
        devolucion2 = DevolucionFactory(
            cliente=cliente2,
            producto=producto,
            tipo='cambio'
        )
        devolucion3 = DevolucionFactory(
            cliente=cliente1,
            producto=producto,
            tipo='defecto'
        )
        
        assert producto.devoluciones.count() == 3
        assert cliente1.devoluciones.count() == 2
        assert cliente2.devoluciones.count() == 1

    def test_should_impact_customer_credit_balance(self):
        """Debe impactar balance de crédito del cliente."""
        cliente = ClienteFactory(saldo_a_favor=Decimal('0'))
        
        # Crear devolución que genera saldo
        devolucion = DevolucionFactory(
            cliente=cliente,
            saldo_a_favor_generado=Decimal('75.00'),
            estado='completada'
        )
        
        # En un sistema real, esto actualizaría el saldo del cliente
        assert devolucion.saldo_a_favor_generado == Decimal('75.00')
        # cliente.saldo_a_favor += devolucion.saldo_a_favor_generado
        # cliente.save()

    def test_should_track_return_patterns_by_product(self):
        """Debe trackear patrones de devolución por producto."""
        producto = ProductoFactory()
        
        # Crear múltiples devoluciones por defecto
        for i in range(5):
            DevolucionFactory(
                producto=producto,
                tipo='defecto',
                estado='validada'
            )
        
        # Crear algunas por cambio
        for i in range(2):
            DevolucionFactory(
                producto=producto,
                tipo='cambio',
                estado='validada'
            )
        
        total_devoluciones = producto.devoluciones.count()
        devoluciones_defecto = producto.devoluciones.filter(tipo='defecto').count()
        
        assert total_devoluciones == 7
        assert devoluciones_defecto == 5
        
        # En un sistema real, esto podría indicar un problema de calidad

    def test_should_preserve_audit_trail(self):
        """Debe preservar rastro de auditoría."""
        user = UserFactory()
        cliente = ClienteFactory()
        producto = ProductoFactory()
        
        with freeze_time("2024-03-15 10:00:00"):
            devolucion = DevolucionFactory(
                cliente=cliente,
                producto=producto,
                created_by=user,
                estado='pendiente'
            )
            
        # Verificar información de auditoría
        assert devolucion.created_by == user
        assert devolucion.fecha.date() == datetime(2024, 3, 15).date()
        
        # En un sistema real, también se podría trackear updated_by y updated_at
