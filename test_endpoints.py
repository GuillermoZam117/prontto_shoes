#!/usr/bin/env python
"""
Test web endpoints accessibility
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from django.test import Client

def test_endpoints():
    """Test key web endpoints"""
    print("🌐 Testing Web Endpoints...")
    
    client = Client()
    
    endpoints = [
        ('/', 'Home page'),
        ('/caja/movimientos/', 'Cash register movements'),
        ('/ventas/pos/', 'POS interface'),
        ('/sincronizacion/api/estadisticas/', 'Sync API'),
        ('/clientes/', 'Clients list'),
    ]
    
    for url, name in endpoints:
        try:
            response = client.get(url)
            status = '✅' if response.status_code in [200, 302] else '❌'
            print(f'{status} {name} ({url}) -> {response.status_code}')
        except Exception as e:
            print(f'❌ {name} ({url}) -> Error: {e}')
    
    print("\n🎯 All critical endpoints tested!")

if __name__ == '__main__':
    test_endpoints()
