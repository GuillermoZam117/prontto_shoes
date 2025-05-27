#!/usr/bin/env python
"""
Test script to verify the frontend API fix using Django test client
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

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from ventas.models import Pedido
from productos.models import Producto
from clientes.models import Cliente
from caja.models import Caja, Tienda
from proveedores.models import Proveedor
from inventario.models import Inventario

def test_frontend_fix():
    """Test the frontend API fix using Django test client"""
    print("🧪 Testing Frontend API Fix with Django test client...")
    
    # Create test user
    user = User.objects.create_user(username='testapi', password='testpass')
    
    # Create test data
    tienda = Tienda.objects.create(nombre='API Test Tienda', direccion='Test Address')
    cliente = Cliente.objects.create(nombre='API Test Cliente', tienda=tienda)
    proveedor = Proveedor.objects.create(nombre='API Test Proveedor')
    
    producto = Producto.objects.create(
        codigo='APITEST001',
        marca='API Test Brand',
        modelo='API Test Model',
        color='API Test Color',
        propiedad='API Test Size',
        costo=100.0,
        precio=150.0,
        numero_pagina='1',
        temporada='Test Season',
        proveedor=proveedor,
        tienda=tienda
    )
    
    # Create inventory
    Inventario.objects.create(
        tienda=tienda,
        producto=producto,
        cantidad_actual=10
    )
    
    # Create caja (required for sales)
    Caja.objects.create(
        tienda=tienda,
        fecha=date.today(),
        fondo_inicial=1000.0,
        cerrada=False
    )
    
    # Create Django test client and login
    client = Client()
    client.login(username='testapi', password='testpass')
    
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
    url = reverse('pedido-list')  # This should be '/api/pedidos/'
    response = client.post(
        url,
        data=json.dumps(test_data),
        content_type='application/json',
        HTTP_X_REQUESTED_WITH='XMLHttpRequest'
    )
    
    print(f"\n📥 Response:")
    print(f"   Status: {response.status_code}")
    print(f"   URL: {url}")
    
    if response.status_code == 201:
        response_data = json.loads(response.content)
        print("✅ SUCCESS: API call worked!")
        print(f"   Created pedido ID: {response_data['id']}")
        print(f"   Response data: {json.dumps(response_data, indent=2, default=str)}")
        
        # Verify the pedido was created correctly
        pedido = Pedido.objects.get(id=response_data['id'])
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
        try:
            error_data = json.loads(response.content)
            print(f"   Response: {json.dumps(error_data, indent=2)}")
        except:
            print(f"   Response content: {response.content.decode()}")
        return False

if __name__ == '__main__':
    success = test_frontend_fix()
    if success:
        print("\n🎉 Frontend API fix verification PASSED!")
    else:
        print("\n💥 Frontend API fix verification FAILED!")
