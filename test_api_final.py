#!/usr/bin/env python
"""
Final API Test - Test the fixed PedidoSerializer
"""
import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from tiendas.models import Tienda
from productos.models import Producto, Catalogo
from inventario.models import Inventario
from caja.models import Caja
from ventas.models import Pedido, DetallePedido
import json
from decimal import Decimal

def test_pedido_api_directly():
    """Test the Pedido API endpoint directly"""
    print("🧪 Testing Pedido API Endpoint...")
    
    try:
        # Create test data
        user = User.objects.create_user(username='test_user', password='test_pass')
        tienda = Tienda.objects.create(nombre='Test Store', direccion='Test Address')
        catalogo = Catalogo.objects.create(nombre='Test Catalog')
        producto = Producto.objects.create(
            codigo='TEST001',
            nombre='Test Product',
            precio=Decimal('100.00'),
            catalogo=catalogo
        )
        
        # Create inventory
        inventario = Inventario.objects.create(
            tienda=tienda,
            producto=producto,
            cantidad_actual=10
        )
        
        # Create open cash box
        caja = Caja.objects.create(
            tienda=tienda,
            fondo_inicial=Decimal('1000.00'),
            cerrada=False
        )
        
        # Create API client
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Test data
        pedido_data = {
            "cliente": None,
            "tienda": tienda.id,
            "tipo": "venta",
            "pagado": True,
            "detalles": [
                {
                    "producto": producto.id,  # This should work now
                    "cantidad": 2
                }
            ]
        }
        
        # Make POST request
        url = reverse('pedido-list')
        response = client.post(url, data=json.dumps(pedido_data), content_type='application/json')
        
        print(f"   📡 API Response Status: {response.status_code}")
        
        if response.status_code == 201:
            print("   ✅ API endpoint working correctly!")
            response_data = response.json()
            print(f"   📦 Created Pedido ID: {response_data.get('id')}")
            print(f"   💰 Total: ${response_data.get('total', 0)}")
            return True
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   📄 Response: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Final API Test - PedidoSerializer Fix Verification")
    print("=" * 60)
    
    success = test_pedido_api_directly()
    
    print("=" * 60)
    if success:
        print("✅ API TEST PASSED - The 400 Bad Request error has been FIXED!")
        sys.exit(0)
    else:
        print("❌ API TEST FAILED - There are still issues to resolve")
        sys.exit(1)
