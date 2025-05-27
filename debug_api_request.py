#!/usr/bin/env python
"""
Debug script to test the Pedido API endpoint directly.
This script simulates the exact request being made from the frontend.
"""

import os
import sys
import django
import json
from decimal import Decimal
from datetime import datetime

# Setup Django environment
sys.path.append('c:\\catalog_pos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'catalog_pos.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from django.test.utils import override_settings

# Import models
from ventas.models import Pedido
from productos.models import Producto
from clientes.models import Cliente
from caja.models import Caja, Tienda

def test_api_request():
    """Test the exact API request being made from the frontend"""
    
    print("=== DEBUG: Testing Pedido API Request ===")
    
    # Create test client
    client = APIClient()
    
    # Create or get test user
    try:
        user = User.objects.get(username='testuser')
        print(f"Using existing test user: {user.username}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        print(f"Created test user: {user.username}")
    
    # Login
    client.force_authenticate(user=user)
    
    # Get test data
    try:
        # Get or create a test tienda
        tienda = Tienda.objects.first()
        if not tienda:
            print("ERROR: No tienda found in database")
            return
        
        # Get or create a test producto
        producto = Producto.objects.first()
        if not producto:
            print("ERROR: No producto found in database")
            return
        
        # Get or create a test cliente (or use None for público en general)
        cliente = Cliente.objects.first()
        
        print(f"Test data:")
        print(f"  - Tienda: {tienda.nombre} (ID: {tienda.id})")
        print(f"  - Producto: {producto.codigo} - {producto.nombre} (ID: {producto.id})")
        print(f"  - Cliente: {cliente.nombre if cliente else 'None (público en general)'} (ID: {cliente.id if cliente else 'None'})")
        
    except Exception as e:
        print(f"ERROR getting test data: {e}")
        return
    
    # Create test request data - exactly like frontend sends
    test_data = {
        "cliente": cliente.id if cliente else None,  # This should trigger "público en general"
        "tipo": "venta",
        "descuento_aplicado": 0.0,
        "total": 100.0,
        "tienda": tienda.id,
        "fecha": datetime.now().isoformat(),
        "estado": "completado",
        "detalles": [
            {
                "producto": producto.id,
                "cantidad": 1,
                "precio_unitario": float(producto.precio),
                "subtotal": float(producto.precio)
            }
        ]
    }
    
    print(f"\nRequest data:")
    print(json.dumps(test_data, indent=2, default=str))
    
    # Make the API request
    url = '/api/pedidos/'
    print(f"\nMaking POST request to: {url}")
    
    try:
        response = client.post(
            url,
            data=test_data,
            format='json'
        )
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.items())}")
        
        if response.status_code == 400:
            print(f"ERROR Response content: {response.content.decode()}")
            try:
                error_data = response.json()
                print(f"ERROR Response JSON: {json.dumps(error_data, indent=2)}")
            except:
                print("Could not parse error response as JSON")
        elif response.status_code == 201:
            print(f"SUCCESS Response: {response.json()}")
        else:
            print(f"Response content: {response.content.decode()}")
            
    except Exception as e:
        print(f"Exception during request: {e}")
        import traceback
        traceback.print_exc()

def test_serializer_directly():
    """Test the serializer directly with the same data"""
    
    print("\n=== DEBUG: Testing PedidoSerializer Directly ===")
    
    from ventas.serializers import PedidoSerializer
    from rest_framework.request import Request
    from django.test import RequestFactory
    from django.contrib.auth.models import User
    
    # Get test data
    try:
        tienda = Tienda.objects.first()
        producto = Producto.objects.first()
        cliente = Cliente.objects.first()
        user = User.objects.first()
        
        if not all([tienda, producto, user]):
            print("ERROR: Missing required test data")
            return
            
    except Exception as e:
        print(f"ERROR getting test data: {e}")
        return
    
    # Create test data
    test_data = {
        "cliente": cliente.id if cliente else None,
        "tipo": "venta",
        "descuento_aplicado": 0.0,
        "total": 100.0,
        "tienda": tienda.id,
        "fecha": datetime.now().isoformat(),
        "estado": "completado",
        "pagado": True,
        "detalles": [
            {
                "producto": producto.id,
                "cantidad": 1,
                "precio_unitario": float(producto.precio),
                "subtotal": float(producto.precio)
            }
        ]
    }
    
    # Create mock request
    factory = RequestFactory()
    request = factory.post('/api/pedidos/')
    request.user = user
    
    # Test serializer
    serializer = PedidoSerializer(data=test_data, context={'request': request})
    
    print(f"Serializer data: {test_data}")
    print(f"Is valid: {serializer.is_valid()}")
    
    if not serializer.is_valid():
        print(f"Validation errors: {serializer.errors}")
    else:
        print("Serializer validation passed!")
        try:
            pedido = serializer.save(created_by=user)
            print(f"Pedido created successfully: ID {pedido.id}")
        except Exception as e:
            print(f"Error creating pedido: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_api_request()
    test_serializer_directly()
