#!/usr/bin/env python3
"""
Test script to verify the POS system works with the store fix
"""
import os
import sys
import django
import requests
from django.conf import settings

# Add the Django project directory to the path
sys.path.append('c:/catalog_pos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from products.models import Producto

def test_pos_with_store_1():
    """Test creating an order using store 1 which has an open cash box"""
    
    # Get Django client
    client = Client()
    
    # Login as admin
    user = User.objects.get(username='admin')
    client.force_login(user)
    
    # Get CSRF token
    response = client.get('/ventas/pos/')
    print(f"POS page response: {response.status_code}")
    
    if response.status_code != 200:
        print("❌ Failed to load POS page")
        return False
    
    # Extract CSRF token
    csrf_token = None
    for cookie in response.cookies:
        if cookie.key == 'csrftoken':
            csrf_token = cookie.value
            break
    
    if not csrf_token:
        print("❌ No CSRF token found")
        return False
    
    print(f"✅ CSRF token obtained: {csrf_token[:10]}...")
    
    # Get first available product
    producto = Producto.objects.first()
    if not producto:
        print("❌ No products available")
        return False
    
    print(f"✅ Using product: {producto.nombre} (ID: {producto.id})")
    
    # Create order data with store 1 (which has open cash box)
    order_data = {
        'fecha': '2025-05-27',
        'tipo': 'venta',
        'tienda': 1,  # Using store 1 which has open cash box
        'pagado': True,
        'total': 100.00,
        'detalles': [
            {
                'producto': producto.id,
                'cantidad': 1,
                'precio_unitario': 100.00,
                'subtotal': 100.00
            }
        ]
    }
    
    # Make the request
    response = client.post(
        '/api/ventas/pedidos/',
        data=order_data,
        content_type='application/json',
        HTTP_X_CSRFTOKEN=csrf_token
    )
    
    print(f"Order creation response: {response.status_code}")
    
    if response.status_code == 201:
        response_data = response.json()
        print(f"✅ Order created successfully!")
        print(f"Order ID: {response_data.get('id')}")
        print(f"Total: ${response_data.get('total')}")
        return True
    else:
        print(f"❌ Order creation failed: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error details: {error_data}")
        except:
            print(f"Response content: {response.content.decode()}")
        return False

if __name__ == "__main__":
    print("=== TESTING STORE FIX ===")
    print("Testing POS with store 1 (Tienda01) which has open cash box...")
    
    success = test_pos_with_store_1()
    
    if success:
        print("\n🎉 STORE FIX SUCCESSFUL!")
        print("The POS system can now create orders using store 1.")
    else:
        print("\n❌ STORE FIX FAILED")
        print("There may be additional issues to resolve.")
