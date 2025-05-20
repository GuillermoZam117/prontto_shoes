"""
Integration tests for inventory management workflow.
Tests inventory creation, transfers between stores, and adjustments.
"""
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework.test import APIClient
from decimal import Decimal
import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model

from productos.models import Producto
from tiendas.models import Tienda
from proveedores.models import Proveedor
from inventario.models import Inventario, Traspaso, TraspasoItem

User = get_user_model()

class InventoryTransferWorkflowTest(TransactionTestCase):
    """Test the inventory transfer process between stores."""
    
    def setUp(self):
        """Set up test data for each test."""
        # Create test user
        self.user = User.objects.create_user(
            username='inventorytest',
            email='inventory@example.com',
            password='securepass123',
            is_staff=True
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create stores
        self.tienda_origen = Tienda.objects.create(
            nombre="Tienda Origen",
            direccion="Calle Origen 123",
            contacto="555-1111",
            activa=True,
            created_by=self.user
        )
        
        self.tienda_destino = Tienda.objects.create(
            nombre="Tienda Destino",
            direccion="Calle Destino 456",
            contacto="555-2222",
            activa=True,
            created_by=self.user
        )
        
        # Create a supplier
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Inventario",
            contacto="Juan Inventario",
            max_return_days=30,
            created_by=self.user
        )
        
        # Create products for testing
        self.producto1 = Producto.objects.create(
            codigo="INV001",
            marca="Nike",
            modelo="Air Force",
            color="Negro",
            propiedad="Talla 28",
            costo=Decimal('500.00'),
            precio=Decimal('999.99'),
            numero_pagina="1",
            temporada="Verano",
            oferta=False,
            admite_devolucion=True,
            proveedor=self.proveedor,
            tienda=self.tienda_origen
        )
        
        self.producto2 = Producto.objects.create(
            codigo="INV002",
            marca="Adidas",
            modelo="Superstar",
            color="Blanco",
            propiedad="Talla 27",
            costo=Decimal('400.00'),
            precio=Decimal('799.99'),
            numero_pagina="2",
            temporada="Invierno",
            oferta=True,
            admite_devolucion=True,
            proveedor=self.proveedor,
            tienda=self.tienda_origen
        )
        
        # Create initial inventory for both products
        self.inventario1_origen = Inventario.objects.create(
            producto=self.producto1,
            tienda=self.tienda_origen,
            cantidad_actual=20,
            fecha_registro=timezone.now(),
            created_by=self.user
        )
        
        self.inventario2_origen = Inventario.objects.create(
            producto=self.producto2,
            tienda=self.tienda_origen,
            cantidad_actual=15,
            fecha_registro=timezone.now(),
            created_by=self.user
        )
        
        # Create initial inventory at destination store (with 0 quantity)
        self.inventario1_destino = Inventario.objects.create(
            producto=self.producto1,
            tienda=self.tienda_destino,
            cantidad_actual=0,
            fecha_registro=timezone.now(),
            created_by=self.user
        )
        
        self.inventario2_destino = Inventario.objects.create(
            producto=self.producto2,
            tienda=self.tienda_destino,
            cantidad_actual=0,
            fecha_registro=timezone.now(),
            created_by=self.user
        )
    
    def test_inventory_transfer_workflow(self):
        """Test the complete inventory transfer workflow between stores."""
        
        # Step 1: Create a transfer request
        traspaso = Traspaso.objects.create(
            tienda_origen=self.tienda_origen,
            tienda_destino=self.tienda_destino,
            estado='pendiente',
            created_by=self.user
        )
        
        # Step 2: Add products to the transfer
        item1 = TraspasoItem.objects.create(
            traspaso=traspaso,
            producto=self.producto1,
            cantidad=5
        )
        
        item2 = TraspasoItem.objects.create(
            traspaso=traspaso,
            producto=self.producto2,
            cantidad=3
        )
        
        # Step 3: Verify transfer is created with correct products and quantities
        self.assertEqual(traspaso.items.count(), 2)
        self.assertEqual(item1.cantidad, 5)
        self.assertEqual(item2.cantidad, 3)
        
        # Step 4: Process the transfer - Update inventory at both locations
        # This would typically be done in a view or service, simulating here
        for item in traspaso.items.all():
            # Decrease quantity at origin store
            inventario_origen = Inventario.objects.get(
                producto=item.producto,
                tienda=traspaso.tienda_origen
            )
            inventario_origen.cantidad_actual -= item.cantidad
            inventario_origen.save()
            
            # Increase quantity at destination store
            inventario_destino = Inventario.objects.get(
                producto=item.producto,
                tienda=traspaso.tienda_destino
            )
            inventario_destino.cantidad_actual += item.cantidad
            inventario_destino.save()
        
        # Step 5: Mark transfer as completed
        traspaso.estado = 'completado'
        traspaso.save()
        
        # Step 6: Verify the transfer completed successfully
        # Check origin store inventory
        inv1_origen_updated = Inventario.objects.get(
            producto=self.producto1,
            tienda=self.tienda_origen
        )
        self.assertEqual(inv1_origen_updated.cantidad_actual, 15)  # 20 - 5
        
        inv2_origen_updated = Inventario.objects.get(
            producto=self.producto2,
            tienda=self.tienda_origen
        )
        self.assertEqual(inv2_origen_updated.cantidad_actual, 12)  # 15 - 3
        
        # Check destination store inventory
        inv1_destino_updated = Inventario.objects.get(
            producto=self.producto1,
            tienda=self.tienda_destino
        )
        self.assertEqual(inv1_destino_updated.cantidad_actual, 5)  # 0 + 5
        
        inv2_destino_updated = Inventario.objects.get(
            producto=self.producto2,
            tienda=self.tienda_destino
        )
        self.assertEqual(inv2_destino_updated.cantidad_actual, 3)  # 0 + 3
        
        # Check transfer status
        self.assertEqual(Traspaso.objects.get(id=traspaso.id).estado, 'completado')


class InventoryAdjustmentWorkflowTest(TransactionTestCase):
    """Test the inventory adjustment workflow for discrepancies."""
    
    def setUp(self):
        """Set up test data for each test."""
        # Create test user
        self.user = User.objects.create_user(
            username='adjustmenttest',
            email='adjustment@example.com',
            password='securepass123',
            is_staff=True
        )
        
        # Set up API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # Create a store
        self.tienda = Tienda.objects.create(
            nombre="Tienda Ajustes",
            direccion="Calle Ajuste 123",
            contacto="555-4444",
            activa=True,
            created_by=self.user
        )
        
        # Create a supplier
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Ajuste",
            contacto="Juan Ajuste",
            max_return_days=30,
            created_by=self.user
        )
        
        # Create products for testing
        self.producto = Producto.objects.create(
            codigo="ADJ001",
            marca="Puma",
            modelo="Suede",
            color="Azul",
            propiedad="Talla 29",
            costo=Decimal('300.00'),
            precio=Decimal('599.99'),
            numero_pagina="3",
            temporada="Primavera",
            oferta=False,
            admite_devolucion=True,
            proveedor=self.proveedor,
            tienda=self.tienda
        )
        
        # Create initial inventory
        self.inventario = Inventario.objects.create(
            producto=self.producto,
            tienda=self.tienda,
            cantidad_actual=25,
            fecha_registro=timezone.now(),
            created_by=self.user
        )
    
    def test_inventory_adjustment_workflow(self):
        """Test the workflow for adjusting inventory when discrepancies are found."""
        
        # Initial verification
        self.assertEqual(self.inventario.cantidad_actual, 25)
        
        # Step 1: Simulate a physical inventory count that finds a discrepancy
        # In a real application, this might be recorded in an AjusteInventario model
        physical_count = 22  # 3 items are missing
        
        # Step 2: Perform the adjustment (simulating what would happen in a view)
        self.inventario.cantidad_actual = physical_count
        self.inventario.save()
        
        # Step 3: Verify the adjustment was made correctly
        inventario_updated = Inventario.objects.get(id=self.inventario.id)
        self.assertEqual(inventario_updated.cantidad_actual, 22)
        
        # In a real app, we might also record the adjustment in an audit log
        # or specific adjustment model - this would be tested here as well 