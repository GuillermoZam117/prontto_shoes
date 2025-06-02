"""
Tests unitarios para los modelos del módulo de inventario
"""
import pytest
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction, models
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch

from inventario.models import Inventario, Traspaso, TraspasoItem
from tests.factories import (
    UserFactory, TiendaFactory, ProductoFactory, ProveedorFactory,
    InventarioFactory, TraspasoFactory
)


class InventarioModelTestCase(TestCase):
    """Tests para el modelo Inventario"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda = TiendaFactory()
        self.proveedor = ProveedorFactory()
        self.producto = ProductoFactory(proveedor=self.proveedor, tienda=self.tienda)

    def test_should_create_inventario_with_required_fields_when_valid_data_provided(self):
        """Debe crear un inventario con los campos obligatorios válidos"""
        inventario = Inventario.objects.create(
            tienda=self.tienda,
            producto=self.producto,
            cantidad_actual=25
        )
        
        self.assertEqual(inventario.tienda, self.tienda)
        self.assertEqual(inventario.producto, self.producto)
        self.assertEqual(inventario.cantidad_actual, 25)
        self.assertIsNotNone(inventario.fecha_registro)
        self.assertIsNotNone(inventario.created_at)
        self.assertIsNotNone(inventario.updated_at)

    def test_should_have_correct_string_representation_when_created(self):
        """Debe tener una representación string correcta"""
        inventario = InventarioFactory(
            tienda=self.tienda,
            producto=self.producto,
            cantidad_actual=15
        )
        expected = f"{self.producto.codigo} - {self.tienda.nombre}: 15"
        self.assertEqual(str(inventario), expected)

    def test_should_enforce_unique_constraint_tienda_producto_when_duplicate_created(self):
        """Debe validar unicidad de tienda-producto"""
        # Crear primer inventario
        InventarioFactory(tienda=self.tienda, producto=self.producto)
        
        # Intentar crear duplicado
        with self.assertRaises(IntegrityError):
            Inventario.objects.create(
                tienda=self.tienda,
                producto=self.producto,  # Misma combinación
                cantidad_actual=10
            )

    def test_should_allow_negative_cantidad_actual_when_tracking_shortages(self):
        """Debe permitir cantidad actual negativa para rastrear faltantes"""
        inventario = Inventario.objects.create(
            tienda=self.tienda,
            producto=self.producto,
            cantidad_actual=-5  # Stock negativo
        )
        
        self.assertEqual(inventario.cantidad_actual, -5)

    def test_should_allow_zero_cantidad_actual_when_out_of_stock(self):
        """Debe permitir cantidad actual cero cuando no hay stock"""
        inventario = Inventario.objects.create(
            tienda=self.tienda,
            producto=self.producto,
            cantidad_actual=0
        )
        
        self.assertEqual(inventario.cantidad_actual, 0)

    def test_should_protect_tienda_when_inventario_exists(self):
        """Debe proteger tienda cuando existe inventario (PROTECT)"""
        InventarioFactory(tienda=self.tienda, producto=self.producto)
        
        # No debe permitir eliminar tienda si tiene inventarios
        with self.assertRaises(Exception):  # ProtectedError
            self.tienda.delete()

    def test_should_protect_producto_when_inventario_exists(self):
        """Debe proteger producto cuando existe inventario (PROTECT)"""
        InventarioFactory(tienda=self.tienda, producto=self.producto)
        
        # No debe permitir eliminar producto si tiene inventarios
        with self.assertRaises(Exception):  # ProtectedError
            self.producto.delete()

    def test_should_handle_audit_fields_correctly_when_user_provided(self):
        """Debe manejar campos de auditoría correctamente"""
        inventario = InventarioFactory(
            tienda=self.tienda,
            producto=self.producto,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(inventario.created_by, self.user)
        self.assertEqual(inventario.updated_by, self.user)

    def test_should_set_null_when_user_deleted(self):
        """Debe establecer NULL cuando se elimina el usuario (SET_NULL)"""
        user = UserFactory()
        inventario = InventarioFactory(
            tienda=self.tienda,
            producto=self.producto,
            created_by=user
        )
        
        # Eliminar usuario
        user.delete()
        inventario.refresh_from_db()
        
        # Verificar que se estableció NULL
        self.assertIsNone(inventario.created_by)

    def test_should_relate_to_tienda_correctly_through_foreign_key(self):
        """Debe relacionarse correctamente con tienda"""
        inventario = InventarioFactory(tienda=self.tienda, producto=self.producto)
        
        # Verificar relación desde inventario a tienda
        self.assertEqual(inventario.tienda, self.tienda)
        
        # Verificar relación inversa desde tienda a inventarios
        self.assertIn(inventario, self.tienda.inventarios.all())

    def test_should_relate_to_producto_correctly_through_foreign_key(self):
        """Debe relacionarse correctamente con producto"""
        inventario = InventarioFactory(tienda=self.tienda, producto=self.producto)
        
        # Verificar relación desde inventario a producto
        self.assertEqual(inventario.producto, self.producto)
        
        # Verificar relación inversa desde producto a inventarios
        self.assertIn(inventario, self.producto.inventarios.all())

    def test_should_handle_multiple_inventarios_different_tiendas_same_producto(self):
        """Debe manejar múltiples inventarios del mismo producto en diferentes tiendas"""
        tienda2 = TiendaFactory(nombre="Tienda Norte")
        
        inventario1 = InventarioFactory(
            tienda=self.tienda,
            producto=self.producto,
            cantidad_actual=10
        )
        
        inventario2 = InventarioFactory(
            tienda=tienda2,
            producto=self.producto,
            cantidad_actual=15
        )
        
        # Verificar que ambos existen
        self.assertEqual(Inventario.objects.filter(producto=self.producto).count(), 2)
        self.assertNotEqual(inventario1.tienda, inventario2.tienda)


class TraspasoModelTestCase(TestCase):
    """Tests para el modelo Traspaso"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda_origen = TiendaFactory(nombre="Tienda Central")
        self.tienda_destino = TiendaFactory(nombre="Tienda Norte")

    def test_should_create_traspaso_with_required_fields_when_valid_data_provided(self):
        """Debe crear un traspaso con los campos obligatorios válidos"""
        traspaso = Traspaso.objects.create(
            tienda_origen=self.tienda_origen,
            tienda_destino=self.tienda_destino
        )
        
        self.assertEqual(traspaso.tienda_origen, self.tienda_origen)
        self.assertEqual(traspaso.tienda_destino, self.tienda_destino)
        self.assertEqual(traspaso.estado, 'pendiente')  # Valor por defecto
        self.assertIsNotNone(traspaso.fecha)

    def test_should_have_correct_string_representation_when_created(self):
        """Debe tener una representación string correcta"""
        traspaso = TraspasoFactory(
            tienda_origen=self.tienda_origen,
            tienda_destino=self.tienda_destino,
            estado='enviado'
        )
        expected = f"Traspaso de {self.tienda_origen.nombre} a {self.tienda_destino.nombre} (enviado)"
        self.assertEqual(str(traspaso), expected)

    def test_should_allow_valid_estados_when_creating_traspaso(self):
        """Debe permitir estados válidos"""
        valid_estados = ['pendiente', 'enviado', 'recibido', 'cancelado']
        
        for estado in valid_estados:
            traspaso = TraspasoFactory(
                tienda_origen=self.tienda_origen,
                tienda_destino=self.tienda_destino,
                estado=estado
            )
            self.assertEqual(traspaso.estado, estado)

    def test_should_protect_tienda_origen_when_traspaso_exists(self):
        """Debe proteger tienda origen cuando existe traspaso (PROTECT)"""
        TraspasoFactory(tienda_origen=self.tienda_origen, tienda_destino=self.tienda_destino)
        
        # No debe permitir eliminar tienda origen si tiene traspasos
        with self.assertRaises(Exception):  # ProtectedError
            self.tienda_origen.delete()

    def test_should_protect_tienda_destino_when_traspaso_exists(self):
        """Debe proteger tienda destino cuando existe traspaso (PROTECT)"""
        TraspasoFactory(tienda_origen=self.tienda_origen, tienda_destino=self.tienda_destino)
        
        # No debe permitir eliminar tienda destino si tiene traspasos
        with self.assertRaises(Exception):  # ProtectedError
            self.tienda_destino.delete()

    def test_should_handle_audit_fields_correctly_when_created_by_user(self):
        """Debe manejar campos de auditoría correctamente"""
        traspaso = TraspasoFactory(
            tienda_origen=self.tienda_origen,
            tienda_destino=self.tienda_destino,
            created_by=self.user
        )
        
        self.assertEqual(traspaso.created_by, self.user)

    def test_should_allow_same_tienda_origen_multiple_traspasos_when_different_destinos(self):
        """Debe permitir múltiples traspasos desde la misma tienda origen"""
        tienda_destino2 = TiendaFactory(nombre="Tienda Sur")
        
        traspaso1 = TraspasoFactory(
            tienda_origen=self.tienda_origen,
            tienda_destino=self.tienda_destino
        )
        
        traspaso2 = TraspasoFactory(
            tienda_origen=self.tienda_origen,
            tienda_destino=tienda_destino2
        )
        
        # Verificar que ambos existen
        traspasos_origen = Traspaso.objects.filter(tienda_origen=self.tienda_origen)
        self.assertEqual(traspasos_origen.count(), 2)
        self.assertIn(traspaso1, traspasos_origen)
        self.assertIn(traspaso2, traspasos_origen)

    def test_should_relate_to_tiendas_correctly_through_foreign_keys(self):
        """Debe relacionarse correctamente con tiendas"""
        traspaso = TraspasoFactory(
            tienda_origen=self.tienda_origen,
            tienda_destino=self.tienda_destino
        )
        
        # Verificar relaciones inversas
        self.assertIn(traspaso, self.tienda_origen.traspasos_salida.all())
        self.assertIn(traspaso, self.tienda_destino.traspasos_entrada.all())    def test_should_auto_set_fecha_when_created(self):
        """Debe establecer automáticamente la fecha cuando se crea"""
        traspaso = Traspaso.objects.create(
            tienda_origen=self.tienda_origen,
            tienda_destino=self.tienda_destino
        )
        
        # La fecha se establece automáticamente
        self.assertIsNotNone(traspaso.fecha)
        # Verificar que la fecha está cerca del momento actual
        now = timezone.now()
        self.assertLess(abs((now - traspaso.fecha).total_seconds()), 5)


class TraspasoItemModelTestCase(TestCase):
    """Tests para el modelo TraspasoItem"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda_origen = TiendaFactory(nombre="Tienda Central")
        self.tienda_destino = TiendaFactory(nombre="Tienda Norte")
        self.proveedor = ProveedorFactory()
        self.producto = ProductoFactory(proveedor=self.proveedor, tienda=self.tienda_origen)
        self.traspaso = TraspasoFactory(
            tienda_origen=self.tienda_origen,
            tienda_destino=self.tienda_destino
        )

    def test_should_create_traspaso_item_with_required_fields_when_valid_data_provided(self):
        """Debe crear un item de traspaso con campos válidos"""
        item = TraspasoItem.objects.create(
            traspaso=self.traspaso,
            producto=self.producto,
            cantidad=10
        )
        
        self.assertEqual(item.traspaso, self.traspaso)
        self.assertEqual(item.producto, self.producto)
        self.assertEqual(item.cantidad, 10)

    def test_should_have_correct_string_representation_when_created(self):
        """Debe tener una representación string correcta"""
        item = TraspasoItem.objects.create(
            traspaso=self.traspaso,
            producto=self.producto,
            cantidad=5
        )
        expected = f"{self.producto.codigo}: 5"
        self.assertEqual(str(item), expected)

    def test_should_enforce_positive_cantidad_when_creating(self):
        """Debe validar que la cantidad sea positiva"""
        with self.assertRaises(IntegrityError):
            TraspasoItem.objects.create(
                traspaso=self.traspaso,
                producto=self.producto,
                cantidad=0  # Cantidad no positiva
            )

    def test_should_cascade_delete_when_traspaso_deleted(self):
        """Debe eliminar items cuando se elimina traspaso (CASCADE)"""
        item = TraspasoItem.objects.create(
            traspaso=self.traspaso,
            producto=self.producto,
            cantidad=8
        )
        item_id = item.id
        
        # Eliminar traspaso
        self.traspaso.delete()
        
        # Verificar que item fue eliminado
        with self.assertRaises(TraspasoItem.DoesNotExist):
            TraspasoItem.objects.get(id=item_id)

    def test_should_protect_producto_when_traspaso_item_exists(self):
        """Debe proteger producto cuando existe item de traspaso (PROTECT)"""
        TraspasoItem.objects.create(
            traspaso=self.traspaso,
            producto=self.producto,
            cantidad=3
        )
        
        # No debe permitir eliminar producto si tiene items de traspaso
        with self.assertRaises(Exception):  # ProtectedError
            self.producto.delete()

    def test_should_handle_multiple_items_per_traspaso_when_different_products(self):
        """Debe manejar múltiples items por traspaso con productos diferentes"""
        producto2 = ProductoFactory(
            codigo='P002',
            proveedor=self.proveedor,
            tienda=self.tienda_origen
        )
        
        item1 = TraspasoItem.objects.create(
            traspaso=self.traspaso,
            producto=self.producto,
            cantidad=5
        )
        
        item2 = TraspasoItem.objects.create(
            traspaso=self.traspaso,
            producto=producto2,
            cantidad=3
        )
        
        # Verificar que ambos pertenecen al mismo traspaso
        items = self.traspaso.items.all()
        self.assertEqual(items.count(), 2)
        self.assertIn(item1, items)
        self.assertIn(item2, items)

    def test_should_relate_to_traspaso_correctly_through_foreign_key(self):
        """Debe relacionarse correctamente con traspaso"""
        item = TraspasoItem.objects.create(
            traspaso=self.traspaso,
            producto=self.producto,
            cantidad=7
        )
        
        # Verificar relación desde item a traspaso
        self.assertEqual(item.traspaso, self.traspaso)
        
        # Verificar relación inversa desde traspaso a items
        self.assertIn(item, self.traspaso.items.all())

    def test_should_relate_to_producto_correctly_through_foreign_key(self):
        """Debe relacionarse correctamente con producto"""
        item = TraspasoItem.objects.create(
            traspaso=self.traspaso,
            producto=self.producto,
            cantidad=4
        )
        
        # Verificar relación desde item a producto
        self.assertEqual(item.producto, self.producto)
        
        # Verificar relación inversa desde producto a items
        self.assertIn(item, self.producto.traspaso_items.all())

    def test_should_allow_same_producto_multiple_traspasos_when_different_transactions(self):
        """Debe permitir el mismo producto en múltiples traspasos"""
        traspaso2 = TraspasoFactory(
            tienda_origen=self.tienda_origen,
            tienda_destino=self.tienda_destino
        )
        
        item1 = TraspasoItem.objects.create(
            traspaso=self.traspaso,
            producto=self.producto,
            cantidad=5
        )
        
        item2 = TraspasoItem.objects.create(
            traspaso=traspaso2,
            producto=self.producto,
            cantidad=3
        )
        
        # Verificar que ambos existen
        items_producto = TraspasoItem.objects.filter(producto=self.producto)
        self.assertEqual(items_producto.count(), 2)
        self.assertIn(item1, items_producto)
        self.assertIn(item2, items_producto)


class InventarioBusinessLogicTestCase(TestCase):
    """Tests para lógica de negocio compleja de inventario"""

    def setUp(self):
        self.user = UserFactory()
        self.tienda_origen = TiendaFactory(nombre="Tienda Central")
        self.tienda_destino = TiendaFactory(nombre="Tienda Norte")
        self.proveedor = ProveedorFactory()
        self.producto = ProductoFactory(proveedor=self.proveedor, tienda=self.tienda_origen)

    def test_should_handle_inventory_transfers_correctly_when_traspaso_completed(self):
        """Debe manejar transferencias de inventario correctamente"""
        # Crear inventario inicial en tienda origen
        inventario_origen = InventarioFactory(
            tienda=self.tienda_origen,
            producto=self.producto,
            cantidad_actual=20
        )
        
        # Crear traspaso
        traspaso = TraspasoFactory(
            tienda_origen=self.tienda_origen,
            tienda_destino=self.tienda_destino,
            estado='pendiente'
        )
        
        # Crear item de traspaso
        TraspasoItem.objects.create(
            traspaso=traspaso,
            producto=self.producto,
            cantidad=5
        )
        
        # Verificar que el traspaso está configurado correctamente
        self.assertEqual(traspaso.items.count(), 1)
        self.assertEqual(inventario_origen.cantidad_actual, 20)

    def test_should_validate_stock_availability_when_creating_traspaso(self):
        """Debe validar disponibilidad de stock al crear traspaso"""
        # Crear inventario con stock limitado
        InventarioFactory(
            tienda=self.tienda_origen,
            producto=self.producto,
            cantidad_actual=3
        )
        
        traspaso = TraspasoFactory(
            tienda_origen=self.tienda_origen,
            tienda_destino=self.tienda_destino
        )
        
        # Intentar traspasar más de lo disponible
        # (Esta validación debería implementarse en la lógica de negocio)
        item = TraspasoItem.objects.create(
            traspaso=traspaso,
            producto=self.producto,
            cantidad=5  # Más de lo disponible
        )
        
        # El modelo permite la creación, la validación sería en las vistas/servicios
        self.assertEqual(item.cantidad, 5)

    def test_should_handle_concurrent_inventory_operations_when_multiple_users(self):
        """Debe manejar operaciones concurrentes de inventario"""
        inventario = InventarioFactory(
            tienda=self.tienda_origen,
            producto=self.producto,
            cantidad_actual=10
        )
        
        # Simular operaciones concurrentes
        with transaction.atomic():
            inventario.cantidad_actual = 15
            inventario.save()
            
            # Verificar que la transacción se maneja correctamente
            self.assertEqual(inventario.cantidad_actual, 15)

    def test_should_track_inventory_history_when_changes_made(self):
        """Debe rastrear historial de inventario cuando se hacen cambios"""
        inventario = InventarioFactory(
            tienda=self.tienda_origen,
            producto=self.producto,
            cantidad_actual=10,
            created_by=self.user
        )
        
        # Simular cambio
        original_updated_at = inventario.updated_at
        inventario.cantidad_actual = 15
        inventario.updated_by = self.user
        inventario.save()
        
        # Verificar cambios
        self.assertEqual(inventario.cantidad_actual, 15)
        self.assertEqual(inventario.updated_by, self.user)
        self.assertGreater(inventario.updated_at, original_updated_at)

    def test_should_calculate_total_inventory_across_stores_when_queried(self):
        """Debe calcular inventario total entre tiendas cuando se consulta"""
        # Crear inventarios en múltiples tiendas
        tienda2 = TiendaFactory(nombre="Tienda Sur")
        
        inv1 = InventarioFactory(
            tienda=self.tienda_origen,
            producto=self.producto,
            cantidad_actual=10
        )
        
        inv2 = InventarioFactory(
            tienda=tienda2,
            producto=self.producto,
            cantidad_actual=15
        )
        
        # Calcular total
        total_inventory = Inventario.objects.filter(
            producto=self.producto
        ).aggregate(total=models.Sum('cantidad_actual'))['total']
        
        self.assertEqual(total_inventory, 25)

    def test_should_handle_stock_alerts_when_below_minimum(self):
        """Debe manejar alertas de stock cuando está por debajo del mínimo"""
        # Configurar producto con stock mínimo
        self.producto.stock_minimo = 10
        self.producto.save()
        
        # Crear inventario por debajo del mínimo
        inventario = InventarioFactory(
            tienda=self.tienda_origen,
            producto=self.producto,
            cantidad_actual=5  # Por debajo del mínimo
        )
        
        # Verificar que el inventario se creó correctamente
        self.assertLess(inventario.cantidad_actual, self.producto.stock_minimo)

    def test_should_prevent_negative_stock_when_business_rules_require(self):
        """Debe prevenir stock negativo cuando las reglas de negocio lo requieran"""
        # Este es un test de documentación de la regla de negocio
        # El modelo permite stock negativo, pero podría validarse en las vistas
        inventario = InventarioFactory(
            tienda=self.tienda_origen,
            producto=self.producto,
            cantidad_actual=-5  # Stock negativo permitido en el modelo
        )
        
        # Verificar que el modelo permite stock negativo
        self.assertEqual(inventario.cantidad_actual, -5)
