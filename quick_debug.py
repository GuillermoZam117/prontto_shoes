#!/usr/bin/env python
"""
Quick debug script to test the specific API issue.
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
from rest_framework.test import APIClient
from ventas.models import Pedido
from productos.models import Producto
from clientes.models import Cliente
from caja.models import Tienda, Caja

def debug_api_call():
    """Debug the exact API call"""
    
    print("=== Quick API Debug ===")
    
    client = APIClient()
    
    # Get or create user
    try:
        user = User.objects.get(username='admin')
    except User.DoesNotExist:
        user = User.objects.create_user('admin', 'admin@test.com', 'admin123')
    
    client.force_authenticate(user=user)
    
    # Get test data
    tienda = Tienda.objects.first()
    producto = Producto.objects.first()
    cliente = Cliente.objects.first()
    
    print(f"Data found:")
    print(f"  - Tienda: {tienda.id if tienda else 'None'}")
    print(f"  - Producto: {producto.id if producto else 'None'}")
    print(f"  - Cliente: {cliente.id if cliente else 'None'}")
    
    if not all([tienda, producto]):
        print("Missing required data, cannot test")
        return
    
    # Test data exactly like frontend sends
    request_data = {
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
    
    print(f"\nRequest data:")
    print(json.dumps(request_data, indent=2, default=str))
    
    try:
        response = client.post('/api/pedidos/', request_data, format='json')
        print(f"\nResponse status: {response.status_code}")
        print(f"Response data: {response.content.decode()}")
        
        if response.status_code == 400:
            try:
                error_json = response.json()
                print(f"Error details: {json.dumps(error_json, indent=2)}")
            except:
                print("Could not parse response as JSON")
                
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api_call()
