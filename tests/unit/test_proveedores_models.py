"""
Tests unitarios para modelos de proveedores.
Valida la funcionalidad de Proveedor, PurchaseOrder y PurchaseOrderItem.
"""
import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from freezegun import freeze_time
from datetime import datetime, timedelta

from tests.base import BaseTestCase
from tests.factories import (
    ProveedorFactory, PurchaseOrderFactory, PurchaseOrderItemFactory,
    ProductoFactory, TiendaFactory, UserFactory
)
from proveedores.models import Proveedor, PurchaseOrder, PurchaseOrderItem


class TestProveedorModel(BaseTestCase):
    """Tests unitarios para el modelo Proveedor."""

    def test_should_create_proveedor_with_required_fields(self):
        """Debe crear proveedor con campos requeridos."""
        proveedor = ProveedorFactory(
            nombre="Proveedor Test",
            contacto="contacto@test.com"
        )
        
        assert proveedor.nombre == "Proveedor Test"
        assert proveedor.contacto == "contacto@test.com"
        assert not proveedor.requiere_anticipo
        assert proveedor.max_return_days == 0
        assert proveedor.created_at is not None
        assert proveedor.updated_at is not None

    def test_should_enforce_unique_nombre(self):
        """Debe enforcar unicidad de nombre de proveedor."""
        ProveedorFactory(nombre="Proveedor Único")
        
        with pytest.raises(IntegrityError):
            ProveedorFactory(nombre="Proveedor Único")

    def test_should_create_proveedor_with_anticipo_required(self):
        """Debe crear proveedor que requiere anticipo."""
        proveedor = ProveedorFactory(
            requiere_anticipo=True,
            max_return_days=30
        )
        
        assert proveedor.requiere_anticipo
        assert proveedor.max_return_days == 30

    def test_should_handle_blank_contacto(self):
        """Debe manejar contacto en blanco."""
        proveedor = ProveedorFactory(contacto="")
        
        assert proveedor.contacto == ""
        assert str(proveedor) == proveedor.nombre

    def test_should_track_created_by_and_updated_by(self):
        """Debe trackear quién creó y actualizó el proveedor."""
        user = UserFactory()
        proveedor = ProveedorFactory(
            created_by=user,
            updated_by=user
        )
        
        assert proveedor.created_by == user
        assert proveedor.updated_by == user

    def test_should_handle_null_users_on_deletion(self):
        """Debe manejar eliminación de usuarios (SET_NULL)."""
        user = UserFactory()
        proveedor = ProveedorFactory(created_by=user)
        
        user.delete()
        proveedor.refresh_from_db()
        
        assert proveedor.created_by is None

    @freeze_time("2024-01-15 10:30:00")
    def test_should_set_automatic_timestamps(self):
        """Debe establecer timestamps automáticamente."""
        proveedor = ProveedorFactory()
        
        expected_datetime = datetime(2024, 1, 15, 10, 30, 0)
        assert proveedor.created_at.replace(tzinfo=None) == expected_datetime
        assert proveedor.updated_at.replace(tzinfo=None) == expected_datetime

    def test_should_return_nombre_as_string_representation(self):
        """Debe retornar nombre como representación string."""
        proveedor = ProveedorFactory(nombre="Test Provider")
        
        assert str(proveedor) == "Test Provider"


class TestPurchaseOrderModel(BaseTestCase):
    """Tests unitarios para el modelo PurchaseOrder."""

    def test_should_create_purchase_order_with_required_fields(self):
        """Debe crear orden de compra con campos requeridos."""
        proveedor = ProveedorFactory()
        tienda = TiendaFactory()
        
        po = PurchaseOrderFactory(
            proveedor=proveedor,
            tienda=tienda
        )
        
        assert po.proveedor == proveedor
        assert po.tienda == tienda
        assert po.estado == 'pendiente'
        assert po.fecha_creacion is not None
        assert po.created_at is not None

    def test_should_validate_estado_choices(self):
        """Debe validar las opciones de estado."""
        po = PurchaseOrderFactory()
        
        valid_states = ['pendiente', 'enviado', 'recibido', 'cancelado']
        for state in valid_states:
            po.estado = state
            po.full_clean()  # No debe lanzar excepción

    def test_should_protect_related_proveedor_and_tienda(self):
        """Debe proteger proveedor y tienda relacionados (PROTECT)."""
        proveedor = ProveedorFactory()
        tienda = TiendaFactory()
        PurchaseOrderFactory(proveedor=proveedor, tienda=tienda)
        
        with pytest.raises(Exception):  # ProtectedError or similar
            proveedor.delete()
            
        with pytest.raises(Exception):
            tienda.delete()

    def test_should_track_created_by_user(self):
        """Debe trackear el usuario que creó la orden."""
        user = UserFactory()
        po = PurchaseOrderFactory(created_by=user)
        
        assert po.created_by == user

    def test_should_handle_null_created_by_on_user_deletion(self):
        """Debe manejar eliminación del usuario creador (SET_NULL)."""
        user = UserFactory()
        po = PurchaseOrderFactory(created_by=user)
        
        user.delete()
        po.refresh_from_db()
        
        assert po.created_by is None

    @freeze_time("2024-02-10 14:45:00")
    def test_should_set_automatic_timestamps(self):
        """Debe establecer timestamps automáticamente."""
        po = PurchaseOrderFactory()
        
        expected_datetime = datetime(2024, 2, 10, 14, 45, 0)
        assert po.fecha_creacion.replace(tzinfo=None) == expected_datetime
        assert po.created_at.replace(tzinfo=None) == expected_datetime

    def test_should_return_formatted_string_representation(self):
        """Debe retornar representación string formateada."""
        proveedor = ProveedorFactory(nombre="ACME Corp")
        po = PurchaseOrderFactory(
            proveedor=proveedor,
            estado='enviado'
        )
        
        expected = f"PO-{po.id} (ACME Corp) - enviado"
        assert str(po) == expected

    def test_should_support_multiple_states_workflow(self):
        """Debe soportar flujo de trabajo con múltiples estados."""
        po = PurchaseOrderFactory(estado='pendiente')
        
        po.estado = 'enviado'
        po.save()
        assert po.estado == 'enviado'
        
        po.estado = 'recibido'
        po.save()
        assert po.estado == 'recibido'


class TestPurchaseOrderItemModel(BaseTestCase):
    """Tests unitarios para el modelo PurchaseOrderItem."""

    def test_should_create_item_with_required_fields(self):
        """Debe crear item con campos requeridos."""
        po = PurchaseOrderFactory()
        producto = ProductoFactory()
        
        item = PurchaseOrderItemFactory(
            purchase_order=po,
            producto=producto,
            cantidad_solicitada=10
        )
        
        assert item.purchase_order == po
        assert item.producto == producto
        assert item.cantidad_solicitada == 10
        assert item.cantidad_recibida == 0

    def test_should_track_cantidad_solicitada_vs_recibida(self):
        """Debe trackear cantidad solicitada vs recibida."""
        item = PurchaseOrderItemFactory(
            cantidad_solicitada=15,
            cantidad_recibida=12
        )
        
        assert item.cantidad_solicitada == 15
        assert item.cantidad_recibida == 12
        
        # Simular recepción completa
        item.cantidad_recibida = item.cantidad_solicitada
        item.save()
        assert item.cantidad_recibida == 15

    def test_should_validate_positive_quantities(self):
        """Debe validar cantidades positivas."""
        item = PurchaseOrderItemFactory()
        
        with pytest.raises(ValidationError):
            item.cantidad_solicitada = 0
            item.full_clean()

    def test_should_protect_related_producto(self):
        """Debe proteger producto relacionado (PROTECT)."""
        producto = ProductoFactory()
        PurchaseOrderItemFactory(producto=producto)
        
        with pytest.raises(Exception):  # ProtectedError
            producto.delete()

    def test_should_cascade_delete_with_purchase_order(self):
        """Debe eliminar items cuando se elimina la orden (CASCADE)."""
        po = PurchaseOrderFactory()
        item1 = PurchaseOrderItemFactory(purchase_order=po)
        item2 = PurchaseOrderItemFactory(purchase_order=po)
        
        item_ids = [item1.id, item2.id]
        po.delete()
        
        for item_id in item_ids:
            assert not PurchaseOrderItem.objects.filter(id=item_id).exists()

    def test_should_link_to_detalle_requisicion_optionally(self):
        """Debe linkear opcionalmente a detalle de requisición."""
        # This would require creating requisicion models/factories
        item = PurchaseOrderItemFactory(detalle_requisicion=None)
        
        assert item.detalle_requisicion is None

    def test_should_return_formatted_string_representation(self):
        """Debe retornar representación string formateada."""
        producto = ProductoFactory(codigo="TEST001")
        po = PurchaseOrderFactory()
        item = PurchaseOrderItemFactory(
            producto=producto,
            purchase_order=po,
            cantidad_solicitada=25
        )
        
        expected = f"TEST001 x 25 (PO-{po.id})"
        assert str(item) == expected

    def test_should_support_partial_receipts(self):
        """Debe soportar recepciones parciales."""
        item = PurchaseOrderItemFactory(
            cantidad_solicitada=100,
            cantidad_recibida=0
        )
        
        # Recepción parcial 1
        item.cantidad_recibida = 30
        item.save()
        assert item.cantidad_recibida == 30
        
        # Recepción parcial 2
        item.cantidad_recibida = 70
        item.save()
        assert item.cantidad_recibida == 70
        
        # Recepción final
        item.cantidad_recibida = 100
        item.save()
        assert item.cantidad_recibida == item.cantidad_solicitada

    def test_should_handle_over_delivery(self):
        """Debe manejar entregas excesivas."""
        item = PurchaseOrderItemFactory(
            cantidad_solicitada=50,
            cantidad_recibida=55  # Más de lo solicitado
        )
        
        assert item.cantidad_recibida > item.cantidad_solicitada
        # En un sistema real, esto podría requerir validación adicional


class TestProveedoresModelIntegration(BaseTestCase):
    """Tests de integración entre modelos de proveedores."""

    def test_should_create_complete_purchase_workflow(self):
        """Debe crear flujo completo de compra."""
        # Crear entidades base
        proveedor = ProveedorFactory(nombre="Distribuidor Central")
        tienda = TiendaFactory(nombre="Tienda Norte")
        user = UserFactory()
        
        # Crear productos
        producto1 = ProductoFactory(codigo="PROD001")
        producto2 = ProductoFactory(codigo="PROD002")
        
        # Crear orden de compra
        po = PurchaseOrderFactory(
            proveedor=proveedor,
            tienda=tienda,
            created_by=user,
            estado='pendiente'
        )
        
        # Agregar items
        item1 = PurchaseOrderItemFactory(
            purchase_order=po,
            producto=producto1,
            cantidad_solicitada=100
        )
        item2 = PurchaseOrderItemFactory(
            purchase_order=po,
            producto=producto2,
            cantidad_solicitada=50
        )
        
        # Verificar relaciones
        assert po.items.count() == 2
        assert item1 in po.items.all()
        assert item2 in po.items.all()
        assert po in proveedor.purchase_orders.all()
        assert po in tienda.purchase_orders.all()

    def test_should_handle_multiple_orders_per_proveedor(self):
        """Debe manejar múltiples órdenes por proveedor."""
        proveedor = ProveedorFactory()
        tienda1 = TiendaFactory()
        tienda2 = TiendaFactory()
        
        po1 = PurchaseOrderFactory(proveedor=proveedor, tienda=tienda1)
        po2 = PurchaseOrderFactory(proveedor=proveedor, tienda=tienda2)
        po3 = PurchaseOrderFactory(proveedor=proveedor, tienda=tienda1)
        
        assert proveedor.purchase_orders.count() == 3
        assert tienda1.purchase_orders.count() == 2
        assert tienda2.purchase_orders.count() == 1

    def test_should_calculate_order_totals_through_items(self):
        """Debe calcular totales de orden a través de items."""
        po = PurchaseOrderFactory()
        
        # Crear items con diferentes cantidades
        PurchaseOrderItemFactory(
            purchase_order=po,
            cantidad_solicitada=10,
            cantidad_recibida=8
        )
        PurchaseOrderItemFactory(
            purchase_order=po,
            cantidad_solicitada=25,
            cantidad_recibida=25
        )
        PurchaseOrderItemFactory(
            purchase_order=po,
            cantidad_solicitada=5,
            cantidad_recibida=0
        )
        
        total_solicitado = sum(item.cantidad_solicitada for item in po.items.all())
        total_recibido = sum(item.cantidad_recibida for item in po.items.all())
        
        assert total_solicitado == 40
        assert total_recibido == 33

    def test_should_support_proveedor_with_return_policy(self):
        """Debe soportar proveedor con política de devoluciones."""
        proveedor = ProveedorFactory(
            requiere_anticipo=True,
            max_return_days=15
        )
        
        po = PurchaseOrderFactory(proveedor=proveedor)
        item = PurchaseOrderItemFactory(
            purchase_order=po,
            cantidad_solicitada=100,
            cantidad_recibida=100
        )
        
        # Verificar que se pueden hacer devoluciones dentro del período
        assert proveedor.max_return_days == 15
        assert proveedor.requiere_anticipo
        
        # En un sistema real, aquí se validaría la fecha de compra
        # vs fecha actual para determinar si se puede devolver
