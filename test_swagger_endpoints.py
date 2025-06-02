#!/usr/bin/env python
"""
Script para verificar si la documentación Swagger incluye nuestros nuevos endpoints
Sistema POS Pronto Shoes
"""

import os
import sys
import django

# Agregar el path del proyecto
sys.path.append('c:/catalog_pos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth.models import User

def test_swagger_documentation():
    """Test para verificar la documentación Swagger"""
    print("=== VERIFICACIÓN DOCUMENTACIÓN SWAGGER ===\n")
    
    client = APIClient()
    
    # Test 1: Schema endpoint
    print("1. Test GET /api/schema/")
    response = client.get('/api/schema/')
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.get('Content-Type', 'Not set')}")
    print()
    
    # Test 2: Swagger UI
    print("2. Test GET /api/docs/")
    response = client.get('/api/docs/')
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.get('Content-Type', 'Not set')}")
    print()
    
    # Test 3: ReDoc
    print("3. Test GET /api/redoc/")
    response = client.get('/api/redoc/')
    print(f"   Status: {response.status_code}")
    print(f"   Content-Type: {response.get('Content-Type', 'Not set')}")
    print()
    
    # Test 4: Verificar que nuestros endpoints aparecen en el schema
    if response.status_code == 200:
        try:
            schema_response = client.get('/api/schema/')
            if schema_response.status_code == 200:
                schema_content = schema_response.content.decode('utf-8')
                
                print("4. Verificando presencia de endpoints en schema:")
                endpoints_to_check = [
                    'ordenes-cliente',
                    'seguimiento-productos', 
                    'entregas-parciales',
                    'notas-credito',
                    'portal-politicas',
                    'productos-compartir'
                ]
                
                for endpoint in endpoints_to_check:
                    if endpoint in schema_content:
                        print(f"   ✅ {endpoint}: Encontrado en schema")
                    else:
                        print(f"   ❌ {endpoint}: No encontrado en schema")
                print()
        except Exception as e:
            print(f"   Error verificando schema: {str(e)}")
            print()
    
    print("=== VERIFICACIÓN COMPLETADA ===")
    print("\nPara acceder a la documentación:")
    print("- Swagger UI: http://localhost:8000/api/docs/")
    print("- ReDoc: http://localhost:8000/api/redoc/")
    print("- Schema JSON: http://localhost:8000/api/schema/")

if __name__ == '__main__':
    test_swagger_documentation()
