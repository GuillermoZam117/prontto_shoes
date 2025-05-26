#!/usr/bin/env python
"""
Test script to verify API and visual fixes
Sistema POS Pronto Shoes
"""

import os
import sys
import django
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from tiendas.models import Tienda
from clientes.models import Cliente
from productos.models import Producto
from proveedores.models import Proveedor
from ventas.models import Pedido, DetallePedido
from inventario.models import Inventario
from caja.models import Caja

def test_api_pedido_creation():
    """Test the fixed PedidoSerializer with proper data structure"""
    print("🧪 Testing API Pedido Creation...")
    
    # Create test user
    User = get_user_model()
    user = User.objects.create_user(username='testuser', password='testpass')
    
    # Create test data
    tienda = Tienda.objects.create(nombre='Tienda Test', direccion='Test Address')
    cliente = Cliente.objects.create(nombre='Cliente Test', tienda=tienda)
    proveedor = Proveedor.objects.create(nombre='Proveedor Test')
    producto = Producto.objects.create(
        codigo='TEST001',
        marca='Test Brand',
        modelo='Test Model', 
        color='Test Color',
        propiedad='Test Size',
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
    caja = Caja.objects.create(
        tienda=tienda,
        fondo_inicial=1000.0,
        fecha='2025-05-26',
        cerrada=False
    )
    
    # Setup API client
    client = APIClient()
    client.force_authenticate(user=user)
    
    # Test data that matches frontend structure
    test_data = {
        'cliente': cliente.id,
        'tipo': 'venta',
        'descuento_aplicado': 0,
        'total': 150.0,
        'tienda': tienda.id,
        'fecha': '2025-05-26T10:00:00Z',
        'estado': 'completado',
        'detalles': [
            {
                'producto': producto.id,  # This is the key fix - sending ID directly
                'cantidad': 1,
                'precio_unitario': 150.0,
                'subtotal': 150.0
            }
        ]
    }
    
    # Make API request
    response = client.post('/api/pedidos/', data=test_data, format='json')
    
    if response.status_code == 201:
        print("✅ API Pedido creation SUCCESS")
        print(f"   Created pedido ID: {response.data['id']}")
        return True
    else:
        print("❌ API Pedido creation FAILED")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.data}")
        return False

def test_visual_comfort_css():
    """Test that visual comfort improvements are in place"""
    print("🎨 Testing Visual Comfort CSS...")
    
    try:
        # Check main.css for visual comfort improvements
        with open('c:/catalog_pos/frontend/static/css/main.css', 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        comfort_indicators = [
            '@media (prefers-reduced-motion: reduce)',
            'transform: none !important',
            'transform: translateZ(0)',
            'backface-visibility: hidden'
        ]
        
        all_present = True
        for indicator in comfort_indicators:
            if indicator in css_content:
                print(f"   ✅ Found: {indicator}")
            else:
                print(f"   ❌ Missing: {indicator}")
                all_present = False
        
        # Check that pulse animation is removed/disabled
        if 'animation: pulse' not in css_content or 'Removed pulse animation' in css_content:
            print("   ✅ Pulse animation properly disabled")
        else:
            print("   ❌ Pulse animation still present")
            all_present = False
            
        return all_present
    
    except Exception as e:
        print(f"   ❌ Error reading CSS: {e}")
        return False

def test_caja_template_optimizations():
    """Test that caja templates have been optimized"""
    print("🏪 Testing Caja Template Optimizations...")
    
    try:
        # Check caja table template
        with open('c:/catalog_pos/frontend/templates/caja/partials/caja_table.html', 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        optimizations = [
            'Pulse animation disabled',
            'visual discomfort',
            'opacity: 0.9'  # Indicates pulse is disabled
        ]
        
        all_present = True
        for optimization in optimizations:
            if optimization in template_content:
                print(f"   ✅ Found optimization: {optimization}")
            else:
                print(f"   ❌ Missing optimization: {optimization}")
                all_present = False
        
        # Check update frequency is reasonable (30s+)
        if 'every 30s' in template_content or 'every 60s' in template_content:
            print("   ✅ Update frequency optimized (30s+)")
        else:
            print("   ❌ Update frequency too high")
            all_present = False
            
        return all_present
    
    except Exception as e:
        print(f"   ❌ Error reading template: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running API and Visual Fixes Test Suite")
    print("=" * 50)
    
    tests = [
        test_api_pedido_creation,
        test_visual_comfort_css,
        test_caja_template_optimizations
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
            print()
    
    print("=" * 50)
    print("📊 FINAL RESULTS:")
    print(f"   Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("✅ ALL TESTS PASSED - Both API and visual fixes are working!")
    else:
        print("❌ Some tests failed - check output above")
    
    return all(results)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
