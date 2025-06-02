"""
Tests unitarios para modelos de tiendas.
Valida la funcionalidad del modelo Tienda.
"""
import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from freezegun import freeze_time
from datetime import datetime

from tests.base import BaseTestCase
from tests.factories import TiendaFactory, UserFactory
from tiendas.models import Tienda


class TestTiendaModel(BaseTestCase):
    """Tests unitarios para el modelo Tienda."""

    def test_should_create_tienda_with_required_fields(self):
        """Debe crear tienda con campos requeridos."""
        tienda = TiendaFactory(
            nombre="Tienda Centro",
            direccion="Av. Principal 123",
            contacto="555-0123"
        )
        
        assert tienda.nombre == "Tienda Centro"
        assert tienda.direccion == "Av. Principal 123"
        assert tienda.contacto == "555-0123"
        assert tienda.activa  # Default True
        assert tienda.created_at is not None
        assert tienda.updated_at is not None

    def test_should_enforce_unique_nombre(self):
        """Debe enforcar unicidad de nombre de tienda."""
        TiendaFactory(nombre="Tienda Única")
        
        with pytest.raises(IntegrityError):
            TiendaFactory(nombre="Tienda Única")

    def test_should_handle_blank_contacto(self):
        """Debe manejar contacto en blanco."""
        tienda = TiendaFactory(contacto="")
        
        assert tienda.contacto == ""

    def test_should_create_inactive_tienda(self):
        """Debe crear tienda inactiva."""
        tienda = TiendaFactory(activa=False)
        
        assert not tienda.activa

    def test_should_track_created_by_and_updated_by(self):
        """Debe trackear quién creó y actualizó la tienda."""
        user = UserFactory()
        tienda = TiendaFactory(
            created_by=user,
            updated_by=user
        )
        
        assert tienda.created_by == user
        assert tienda.updated_by == user

    def test_should_handle_null_users_on_deletion(self):
        """Debe manejar eliminación de usuarios (SET_NULL)."""
        user = UserFactory()
        tienda = TiendaFactory(created_by=user, updated_by=user)
        
        user.delete()
        tienda.refresh_from_db()
        
        assert tienda.created_by is None
        assert tienda.updated_by is None

    @freeze_time("2024-01-10 09:15:00")
    def test_should_set_automatic_timestamps(self):
        """Debe establecer timestamps automáticamente."""
        tienda = TiendaFactory()
        
        expected_datetime = datetime(2024, 1, 10, 9, 15, 0)
        assert tienda.created_at.replace(tzinfo=None) == expected_datetime
        assert tienda.updated_at.replace(tzinfo=None) == expected_datetime

    def test_should_return_nombre_as_string_representation(self):
        """Debe retornar nombre como representación string."""
        tienda = TiendaFactory(nombre="Sucursal Norte")
        
        assert str(tienda) == "Sucursal Norte"

    def test_should_validate_required_fields(self):
        """Debe validar campos requeridos."""
        tienda = Tienda()
        
        with pytest.raises(ValidationError):
            tienda.full_clean()

    def test_should_accept_long_direccion(self):
        """Debe aceptar direcciones largas."""
        direccion_larga = "Av. Libertadores #123, Sector Centro, " \
                         "Entre calles 5 y 6, Edificio Torre Plaza, " \
                         "Local 45-B, Ciudad Capital, Estado Principal"
        
        tienda = TiendaFactory(direccion=direccion_larga)
        
        assert tienda.direccion == direccion_larga
        assert len(tienda.direccion) <= 255  # Max length constraint

    def test_should_handle_different_contact_formats(self):
        """Debe manejar diferentes formatos de contacto."""
        contact_formats = [
            "555-0123",
            "0212-555-0123",
            "+58-212-555-0123",
            "tienda@empresa.com",
            "555-0123 / 555-0124",
            "Ext. 123"
        ]
        
        for contact in contact_formats:
            tienda = TiendaFactory(contacto=contact)
            assert tienda.contacto == contact


class TestTiendaBusinessLogic(BaseTestCase):
    """Tests para lógica de negocio de tiendas."""

    def test_should_activate_and_deactivate_tienda(self):
        """Debe activar y desactivar tienda."""
        tienda = TiendaFactory(activa=True)
        
        # Desactivar
        tienda.activa = False
        tienda.save()
        assert not tienda.activa
        
        # Reactivar
        tienda.activa = True
        tienda.save()
        assert tienda.activa

    def test_should_support_multiple_tiendas_per_user(self):
        """Debe soportar múltiples tiendas por usuario."""
        user = UserFactory()
        
        tienda1 = TiendaFactory(created_by=user, nombre="Tienda 1")
        tienda2 = TiendaFactory(created_by=user, nombre="Tienda 2")
        tienda3 = TiendaFactory(created_by=user, nombre="Tienda 3")
        
        tiendas_creadas = user.tiendas_creadas.all()
        
        assert tiendas_creadas.count() == 3
        assert tienda1 in tiendas_creadas
        assert tienda2 in tiendas_creadas
        assert tienda3 in tiendas_creadas

    def test_should_distinguish_created_by_and_updated_by(self):
        """Debe distinguir entre creador y actualizador."""
        creator = UserFactory(username="creator")
        updater = UserFactory(username="updater")
        
        tienda = TiendaFactory(created_by=creator)
        
        # Actualizar por otro usuario
        tienda.updated_by = updater
        tienda.direccion = "Nueva dirección"
        tienda.save()
        
        assert tienda.created_by == creator
        assert tienda.updated_by == updater

    def test_should_maintain_creation_timestamp_on_updates(self):
        """Debe mantener timestamp de creación en actualizaciones."""
        with freeze_time("2024-01-01 10:00:00"):
            tienda = TiendaFactory()
            original_created_at = tienda.created_at
        
        with freeze_time("2024-01-02 15:30:00"):
            tienda.direccion = "Dirección actualizada"
            tienda.save()
            
        tienda.refresh_from_db()
        
        # created_at no debe cambiar
        assert tienda.created_at == original_created_at
        # updated_at debe cambiar
        assert tienda.updated_at.date() == datetime(2024, 1, 2).date()


class TestTiendaIntegration(BaseTestCase):
    """Tests de integración para tiendas."""

    def test_should_be_referenced_by_other_models(self):
        """Debe ser referenciada por otros modelos."""
        tienda = TiendaFactory()
        
        # Verificar que tiene related_names configurados correctamente
        assert hasattr(tienda, 'inventarios')
        assert hasattr(tienda, 'pedidos')
        assert hasattr(tienda, 'purchase_orders')
        assert hasattr(tienda, 'cajas')
        
        # En un sistema real, estos tendrían datos relacionados

    def test_should_support_multi_store_operations(self):
        """Debe soportar operaciones multi-tienda."""
        tienda_norte = TiendaFactory(nombre="Tienda Norte")
        tienda_sur = TiendaFactory(nombre="Tienda Sur")
        tienda_este = TiendaFactory(nombre="Tienda Este")
        
        todas_tiendas = Tienda.objects.all()
        tiendas_activas = Tienda.objects.filter(activa=True)
        
        assert todas_tiendas.count() == 3
        assert tiendas_activas.count() == 3
        
        # Desactivar una tienda
        tienda_norte.activa = False
        tienda_norte.save()
        
        tiendas_activas = Tienda.objects.filter(activa=True)
        assert tiendas_activas.count() == 2

    def test_should_handle_tienda_name_searches(self):
        """Debe manejar búsquedas por nombre de tienda."""
        TiendaFactory(nombre="Centro Comercial Plaza")
        TiendaFactory(nombre="Plaza del Valle")
        TiendaFactory(nombre="Mercado Central")
        
        # Búsqueda por contenido
        tiendas_plaza = Tienda.objects.filter(nombre__icontains="Plaza")
        tiendas_centro = Tienda.objects.filter(nombre__icontains="Centro")
        
        assert tiendas_plaza.count() == 2
        assert tiendas_centro.count() == 2

    def test_should_preserve_tienda_hierarchy(self):
        """Debe preservar jerarquía de tiendas si existe."""
        # En un sistema real, podría haber tienda matriz y sucursales
        tienda_matriz = TiendaFactory(nombre="Matriz")
        sucursal_1 = TiendaFactory(nombre="Sucursal 1")
        sucursal_2 = TiendaFactory(nombre="Sucursal 2")
        
        # Verificar que todas existen independientemente
        assert Tienda.objects.count() == 3
        assert all(tienda.activa for tienda in Tienda.objects.all())

    def test_should_support_geographical_organization(self):
        """Debe soportar organización geográfica."""
        tiendas_por_region = {
            "Norte": ["Tienda Maracaibo", "Tienda Valencia"],
            "Sur": ["Tienda Puerto Ordaz", "Tienda San Cristóbal"],
            "Centro": ["Tienda Caracas Centro", "Tienda Caracas Este"]
        }
        
        created_tiendas = {}
        for region, nombres in tiendas_por_region.items():
            created_tiendas[region] = []
            for nombre in nombres:
                tienda = TiendaFactory(nombre=nombre)
                created_tiendas[region].append(tienda)
        
        # Verificar creación
        assert Tienda.objects.count() == 6
        
        # En un sistema real, se podría agregar un campo 'region'
        # para facilitar consultas geográficas

    def test_should_maintain_audit_trail(self):
        """Debe mantener rastro de auditoría."""
        creator = UserFactory(username="admin")
        updater = UserFactory(username="manager")
        
        with freeze_time("2024-01-15 08:00:00"):
            tienda = TiendaFactory(
                created_by=creator,
                nombre="Tienda Auditada"
            )
        
        with freeze_time("2024-01-20 14:30:00"):
            tienda.updated_by = updater
            tienda.direccion = "Nueva dirección"
            tienda.save()
        
        # Verificar rastro completo
        assert tienda.created_by.username == "admin"
        assert tienda.updated_by.username == "manager"
        assert tienda.created_at.date() == datetime(2024, 1, 15).date()
        assert tienda.updated_at.date() == datetime(2024, 1, 20).date()

    def test_should_handle_bulk_operations(self):
        """Debe manejar operaciones en lote."""
        # Crear múltiples tiendas
        tiendas = []
        for i in range(10):
            tienda = TiendaFactory(nombre=f"Tienda {i+1}")
            tiendas.append(tienda)
        
        # Desactivar todas en lote
        Tienda.objects.all().update(activa=False)
        
        tiendas_activas = Tienda.objects.filter(activa=True)
        assert tiendas_activas.count() == 0
        
        # Reactivar algunas
        primeras_cinco = Tienda.objects.all()[:5]
        for tienda in primeras_cinco:
            tienda.activa = True
            tienda.save()
        
        tiendas_activas = Tienda.objects.filter(activa=True)
        assert tiendas_activas.count() == 5
