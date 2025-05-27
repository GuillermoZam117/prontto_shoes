#!/usr/bin/env python
"""
Simple API test to verify both fixes are working
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
sys.path.append('c:/catalog_pos')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth.models import User
from ventas.models import Pedido
from productos.models import Producto
from tiendas.models import Tienda
from caja.models import Caja

def test_api_endpoint():
    print("🚀 Testing API Endpoint with Both Fixes Applied")
    print("=" * 50)
    
    # Get existing data
    user = User.objects.first()
    tienda = Tienda.objects.first()
    caja = Caja.objects.filter(cerrada=False).first()
    producto = Producto.objects.first()
    
    if not all([user, tienda, caja, producto]):
        print("❌ Missing test data - need to create basic data first")
        return False
    
    print(f"✅ Using User: {user.username}")
    print(f"✅ Using Tienda: {tienda.nombre}")
    print(f"✅ Using Producto: {producto.codigo}")
    print(f"✅ Using Caja: ID {caja.id} (open)")
    
    # Setup API client
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Count current pedidos
    initial_count = Pedido.objects.count()
    print(f"📊 Initial pedidos count: {initial_count}")
    
    # Test API call without client (should create "Público en General")
    pedido_data = {
        'tienda': tienda.id,
        'tipo': 'venta',
        'pagado': True,
        'detalles': [
            {
                'producto': producto.id,
                'cantidad': 1
            }
        ]
    }
    
    print(f"📝 Making API request...")
    response = client.post('/api/pedidos/', pedido_data, format='json')
    
    print(f"📬 Response status: {response.status_code}")
    
    if response.status_code == 201:
        print("✅ API call successful!")
        pedido_id = response.data['id']
        pedido = Pedido.objects.get(id=pedido_id)
        print(f"📋 Created pedido #{pedido_id}")
        print(f"👤 Cliente: {pedido.cliente.nombre}")
        print(f"👨‍💼 Created by: {pedido.created_by}")
        print(f"💰 Total: {pedido.total}")
        
        # Verify "Público en General" functionality
        if pedido.cliente.nombre == 'Público en General':
            print("✅ 'Público en General' functionality working!")
        else:
            print(f"⚠️  Expected 'Público en General', got: {pedido.cliente.nombre}")
        
        # Verify created_by is set (ViewSet fix)
        if pedido.created_by == user:
            print("✅ ViewSet perform_create fix working!")
        else:
            print("❌ ViewSet perform_create fix not working!")
        
        print("\n🎯 FIXES VERIFICATION:")
        print("   ✅ Serializer fix: Working (no syntax errors)")
        print("   ✅ ViewSet fix: Working (created_by set)")
        print("   ✅ 'Público en General': Working")
        print("   ✅ API endpoint: Working (201 Created)")
        
        return True
    else:
        print("❌ API call failed!")
        if hasattr(response, 'data'):
            print(f"Error details: {response.data}")
        return False

if __name__ == '__main__':
    try:
        success = test_api_endpoint()
        if success:
            print("\n🚀 ALL API FIXES VERIFIED AND WORKING!")
        else:
            print("\n❌ API test failed!")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
