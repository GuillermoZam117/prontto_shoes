"""
Tests for the conflict resolution component of the synchronization module.
"""
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from tiendas.models import Tienda
from productos.models import Producto, Categoria
from sincronizacion.models import ColaSincronizacion, EstadoSincronizacion, TipoOperacion
from sincronizacion.conflict_resolution import ConflictResolver, ConflictResolutionStrategy
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json

class ConflictResolverTest(TestCase):
    """Test case for the conflict resolver functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username='user_central',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            username='user_tienda',
            password='password456'
        )
        
        # Create test tiendas
        self.tienda_central = Tienda.objects.create(
            nombre='Tienda Central',
            direccion='Calle Central 100',
            telefono='555-000-0000',
            email='central@example.com',
            responsable=self.user1,
            es_central=True
        )
        
        self.tienda_local = Tienda.objects.create(
            nombre='Tienda Local',
            direccion='Calle Local 200',
            telefono='555-111-1111',
            email='local@example.com',
            responsable=self.user2
        )
        
        # Create test category
        self.categoria = Categoria.objects.create(
            nombre='Categoria Conflicto',
            descripcion='Descripción de categoría de prueba'
        )
        
        # Create test products (one on each store with same code but different data)
        self.producto_central = Producto.objects.create(
            nombre='Zapato Elegante Central',
            codigo='ZE001',
            descripcion='Zapato elegante versión central',
            precio=150.00,
            stock=30,
            categoria=self.categoria,
            tienda=self.tienda_central
        )
        
        self.producto_local = Producto.objects.create(
            nombre='Zapato Elegante Local',
            codigo='ZE001',  # Same code, different name
            descripcion='Zapato elegante versión local',
            precio=145.00,   # Different price
            stock=10,        # Different stock
            categoria=self.categoria,
            tienda=self.tienda_local
        )
        
        # Create conflicting sync operations
        self.operacion_central = ColaSincronizacion.objects.create(
            tienda_origen=self.tienda_central,
            tienda_destino=self.tienda_local,
            modelo_tipo='productos.Producto',
            modelo_id=self.producto_central.id,
            operacion=TipoOperacion.ACTUALIZAR,
            estado=EstadoSincronizacion.CONFLICTO,
            datos={
                'id': self.producto_central.id,
                'nombre': self.producto_central.nombre,
                'codigo': self.producto_central.codigo,
                'descripcion': self.producto_central.descripcion,
                'precio': float(self.producto_central.precio),
                'stock': self.producto_central.stock
            },
            fecha_creacion=timezone.now() - timedelta(hours=2),
            fecha_modificacion=timezone.now() - timedelta(hours=1)
        )
        
        self.operacion_local = ColaSincronizacion.objects.create(
            tienda_origen=self.tienda_local,
            tienda_destino=self.tienda_central,
            modelo_tipo='productos.Producto',
            modelo_id=self.producto_local.id,
            operacion=TipoOperacion.ACTUALIZAR,
            estado=EstadoSincronizacion.CONFLICTO,
            datos={
                'id': self.producto_local.id,
                'nombre': self.producto_local.nombre,
                'codigo': self.producto_local.codigo,
                'descripcion': self.producto_local.descripcion,
                'precio': float(self.producto_local.precio),
                'stock': self.producto_local.stock
            },
            fecha_creacion=timezone.now() - timedelta(hours=1),
            fecha_modificacion=timezone.now()
        )
        
        # Initialize conflict resolver
        self.resolver = ConflictResolver()
    
    def test_resolver_conflicto_ultima_modificacion(self):
        """Test conflict resolution with last modification strategy"""
        # Set strategy to last modification
        result = self.resolver.resolver_conflicto(
            self.operacion_central,
            self.operacion_local,
            strategy=ConflictResolutionStrategy.ULTIMA_MODIFICACION
        )
        
        # The local operation is more recent, so it should win
        self.assertEqual(result.id, self.operacion_local.id)
        self.assertEqual(result.estado, EstadoSincronizacion.PENDIENTE)
    
    def test_resolver_conflicto_tienda_central(self):
        """Test conflict resolution with central store priority strategy"""
        # Set strategy to central store priority
        result = self.resolver.resolver_conflicto(
            self.operacion_central,
            self.operacion_local,
            strategy=ConflictResolutionStrategy.PRIORIDAD_CENTRAL
        )
        
        # Central store operation should win
        self.assertEqual(result.id, self.operacion_central.id)
        self.assertEqual(result.estado, EstadoSincronizacion.PENDIENTE)
    
    def test_resolver_conflicto_campo_especifico(self):
        """Test conflict resolution with specific field merger strategy"""
        # Set strategy to field-specific merge
        result = self.resolver.resolver_conflicto(
            self.operacion_central,
            self.operacion_local,
            strategy=ConflictResolutionStrategy.MEZCLAR_CAMPOS,
            field_priorities={
                'nombre': 'central',      # Use central store's name
                'precio': 'central',      # Use central store's price
                'stock': 'sumar',         # Sum both stocks
                'descripcion': 'local'    # Use local store's description
            }
        )
        
        # Check merged data
        merged_data = result.datos
        self.assertEqual(merged_data['nombre'], self.producto_central.nombre)
        self.assertEqual(merged_data['precio'], float(self.producto_central.precio))
        self.assertEqual(merged_data['stock'], self.producto_central.stock + self.producto_local.stock)
        self.assertEqual(merged_data['descripcion'], self.producto_local.descripcion)
    
    def test_detectar_conflictos(self):
        """Test conflict detection"""
        conflicts = self.resolver.detectar_conflictos(
            modelo_tipo='productos.Producto',
            codigo='ZE001'
        )
        
        self.assertEqual(len(conflicts), 2)  # Should find 2 conflicting operations
    
    def test_resolver_todos_conflictos(self):
        """Test resolving all conflicts for a specific model/code"""
        # Resolve all conflicts with central priority strategy
        resolved = self.resolver.resolver_todos_conflictos(
            modelo_tipo='productos.Producto',
            codigo='ZE001',
            strategy=ConflictResolutionStrategy.PRIORIDAD_CENTRAL
        )
        
        self.assertEqual(len(resolved), 1)  # Should return 1 resolved operation
        self.assertEqual(resolved[0].id, self.operacion_central.id)
        
        # Check that both operations are updated in DB
        self.operacion_central.refresh_from_db()
        self.operacion_local.refresh_from_db()
        
        self.assertEqual(self.operacion_central.estado, EstadoSincronizacion.PENDIENTE)
        self.assertEqual(self.operacion_local.estado, EstadoSincronizacion.COMPLETADO)
