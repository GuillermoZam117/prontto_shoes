#!/usr/bin/env python
"""
Test script to verify the frontend API fix works correctly.
Simulates the exact request structure now being sent from the frontend.
"""

import os
import sys
import django
import json
from datetime import date

# Setup Django environment
sys.path.append('c:\\catalog_pos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from ventas.models import Pedido
from productos.models import Producto
from clientes.models import Cliente
from caja.models import Caja, Tienda
from proveedores.models import Proveedor
from inventario.models import Inventario

def test_frontend_api_fix():
    """Test the fixed frontend data structure"""
    print("🧪 Testing Frontend API Fix...")
      # Note: Not deleting existing data to avoid foreign key constraints
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@test.com'}
    )
    if created:
        user.set_password('testpass')
        user.save()
    
    # Create test data
    tienda, _ = Tienda.objects.get_or_create(
        nombre='Tienda Test',
        defaults={'direccion': 'Test Address'}
    )
    
    cliente, _ = Cliente.objects.get_or_create(
        nombre='Cliente Test',
        defaults={'tienda': tienda}
    )
    
    proveedor, _ = Proveedor.objects.get_or_create(
        nombre='Proveedor Test'
    )
    
    producto, _ = Producto.objects.get_or_create(
        codigo='TEST001',
        defaults={
            'marca': 'Test Brand',
            'modelo': 'Test Model', 
            'color': 'Test Color',
            'propiedad': 'Test Size',
            'costo': 100.0,
            'precio': 150.0,
            'numero_pagina': '1',
            'temporada': 'Test Season',
            'proveedor': proveedor,
            'tienda': tienda
        }
    )
    
    # Create inventory
    inventario, _ = Inventario.objects.get_or_create(
        tienda=tienda,
        producto=producto,
        defaults={'cantidad_actual': 10}
    )
    
    # Create caja (required for sales)
    caja, _ = Caja.objects.get_or_create(
        tienda=tienda,
        fecha=date.today(),
        defaults={
            'fondo_inicial': 1000.0,
            'cerrada': False
        }
    )
    
    # Setup API client
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Test data - FIXED STRUCTURE (matches what frontend now sends)
    test_data = {
        'fecha': '2025-05-27',  # Simple date format
        'tipo': 'venta',
        'tienda': tienda.id,    # Integer ID
        'pagado': True,         # Boolean for venta
        'cliente': cliente.id,  # Integer ID 
        'detalles': [
            {
                'producto': producto.id,  # Just product ID as integer
                'cantidad': 1             # Just quantity as integer
            }
        ]
    }
    
    print(f"📤 Sending request data:")
    print(json.dumps(test_data, indent=2))
    
    # Make API request
    response = client.post('/api/pedidos/', data=test_data, format='json')
    
    print(f"\n📥 Response:")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 201:
        print("✅ SUCCESS: API call worked!")
        print(f"   Created pedido ID: {response.data['id']}")
        print(f"   Response data: {json.dumps(response.data, indent=2, default=str)}")
        
        # Verify the pedido was created correctly
        pedido = Pedido.objects.get(id=response.data['id'])
        print(f"\n📋 Pedido details:")
        print(f"   Cliente: {pedido.cliente.nombre}")
        print(f"   Tienda: {pedido.tienda.nombre}")
        print(f"   Tipo: {pedido.tipo}")
        print(f"   Estado: {pedido.estado}")
        print(f"   Total: ${pedido.total}")
        print(f"   Pagado: {pedido.pagado}")
        print(f"   Detalles count: {pedido.detalles.count()}")
        
        return True
        
    else:
        print("❌ FAILED: API call failed")
        print(f"   Response: {response.data}")
        return False

if __name__ == '__main__':
    success = test_frontend_api_fix()
    if success:
        print("\n🎉 Frontend API fix verification PASSED!")
    else:
        print("\n💥 Frontend API fix verification FAILED!")
