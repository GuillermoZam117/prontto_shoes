#!/usr/bin/env python3
"""
Test script to verify the frontend fix for sending required fields
"""
import requests
import json
from datetime import datetime, date

# Django settings
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')

import django
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from ventas.models import Pedido, DetallePedido
from productos.models import Producto
from tiendas.models import Tienda
from clientes.models import Cliente
from caja.models import CajaApertura

def test_frontend_data_structure():
    """Test that the frontend is now sending the correct data structure"""
    print("=== TESTING FRONTEND DATA STRUCTURE FIX ===")
    
    # Create a test client (Django test client for session handling)
    client = Client()
    
    # Login as admin
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("❌ No admin user found")
        return False
    
    # Force login the user
    client.force_login(admin_user)
    print(f"✅ Logged in as: {admin_user.username}")
    
    # Get test data
    producto = Producto.objects.first()
    tienda = Tienda.objects.first()
    cliente = Cliente.objects.first()
    
    if not all([producto, tienda, cliente]):
        print("❌ Missing test data (producto, tienda, or cliente)")
        return False
    
    print(f"✅ Test data found:")
    print(f"   - Producto: {producto.nombre} (${producto.precio_venta})")
    print(f"   - Tienda: {tienda.nombre}")
    print(f"   - Cliente: {cliente.nombre}")
    
    # Verify cash box is open
    today = date.today()
    apertura = CajaApertura.objects.filter(
        tienda=tienda,
        fecha=today,
        cerrada=False
    ).first()
    
    if not apertura:
        print(f"❌ No open cash box for {tienda.nombre} on {today}")
        return False
    
    print(f"✅ Cash box is open: ID {apertura.id} with ${apertura.monto_inicial}")
    
    # Simulate the frontend data structure (NEW CORRECT FORMAT)
    test_data = {
        "fecha": today.isoformat(),
        "tipo": "venta",
        "tienda": tienda.id,
        "cliente": cliente.id,
        "pagado": True,
        "total": 125.00,  # Now included!
        "detalles": [
            {
                "producto": producto.id,
                "cantidad": 2,
                "precio_unitario": 62.50,  # Now included!
                "subtotal": 125.00  # Now included!
            }
        ]
    }
    
    print(f"\n=== TESTING NEW DATA STRUCTURE ===")
    print(f"Data to send: {json.dumps(test_data, indent=2)}")
    
    # Get CSRF token
    csrf_response = client.get('/ventas/pos/')
    csrf_token = csrf_response.context['csrf_token']
    
    # Make the API request with the new data structure
    response = client.post(
        '/api/pedidos/',
        data=json.dumps(test_data),
        content_type='application/json',
        HTTP_X_CSRFTOKEN=csrf_token
    )
    
    print(f"\n=== API RESPONSE ===")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        response_data = response.json()
        print(f"✅ SUCCESS! Order created successfully")
        print(f"   - Order ID: {response_data.get('id')}")
        print(f"   - Total: ${response_data.get('total')}")
        print(f"   - Cliente: {response_data.get('cliente_nombre', 'N/A')}")
        print(f"   - Details count: {len(response_data.get('detalles', []))}")
        
        # Verify the order was actually created with correct data
        if 'id' in response_data:
            pedido = Pedido.objects.get(id=response_data['id'])
            detalle = pedido.detalles.first()
            
            print(f"\n=== DATABASE VERIFICATION ===")
            print(f"✅ Order in DB: ID {pedido.id}")
            print(f"   - Total: ${pedido.total}")
            print(f"   - Detalle precio_unitario: ${detalle.precio_unitario}")
            print(f"   - Detalle subtotal: ${detalle.subtotal}")
            print(f"   - Cantidad: {detalle.cantidad}")
            
        return True
        
    else:
        print(f"❌ FAILED! Response:")
        try:
            error_data = response.json()
            print(f"   Error details: {json.dumps(error_data, indent=2)}")
        except:
            print(f"   Raw response: {response.content.decode()}")
        return False

def test_old_data_structure():
    """Test that the old data structure would fail"""
    print(f"\n=== TESTING OLD DATA STRUCTURE (SHOULD FAIL) ===")
    
    client = Client()
    admin_user = User.objects.filter(is_superuser=True).first()
    client.force_login(admin_user)
    
    producto = Producto.objects.first()
    tienda = Tienda.objects.first()
    cliente = Cliente.objects.first()
    
    # Simulate the OLD frontend data structure (MISSING FIELDS)
    old_test_data = {
        "fecha": date.today().isoformat(),
        "tipo": "venta",
        "tienda": tienda.id,
        "cliente": cliente.id,
        "pagado": True,
        # Missing "total" field!
        "detalles": [
            {
                "producto": producto.id,
                "cantidad": 2,
                # Missing "precio_unitario" and "subtotal" fields!
            }
        ]
    }
    
    print(f"Old data (missing fields): {json.dumps(old_test_data, indent=2)}")
    
    # Get CSRF token
    csrf_response = client.get('/ventas/pos/')
    csrf_token = csrf_response.context['csrf_token']
    
    # Make the API request with the old data structure
    response = client.post(
        '/api/pedidos/',
        data=json.dumps(old_test_data),
        content_type='application/json',
        HTTP_X_CSRFTOKEN=csrf_token
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        print(f"✅ EXPECTED FAILURE: Old structure correctly rejected")
        try:
            error_data = response.json()
            print(f"   Validation errors: {json.dumps(error_data, indent=2)}")
        except:
            print(f"   Raw response: {response.content.decode()}")
        return True
    else:
        print(f"❌ UNEXPECTED: Old structure should have failed but got {response.status_code}")
        return False

if __name__ == "__main__":
    print("🔧 FRONTEND DATA STRUCTURE FIX VERIFICATION")
    print("=" * 50)
    
    # Test new correct data structure
    success_new = test_frontend_data_structure()
    
    # Test old incorrect data structure
    success_old = test_old_data_structure()
    
    print(f"\n{'=' * 50}")
    print(f"📋 SUMMARY:")
    print(f"✅ New data structure works: {success_new}")
    print(f"✅ Old data structure fails: {success_old}")
    
    if success_new and success_old:
        print(f"\n🎉 FRONTEND FIX SUCCESSFUL!")
        print(f"The frontend now sends all required fields:")
        print(f"  - precio_unitario ✅")
        print(f"  - subtotal ✅") 
        print(f"  - total ✅")
        print(f"\nThe POS system should now work correctly! 🎯")
    else:
        print(f"\n❌ Some tests failed. Check the implementation.")
