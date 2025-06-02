#!/usr/bin/env python
"""
Script para verificar las URLs del sistema de pedidos avanzados
Sistema POS Pronto Shoes
"""

import os
import sys
import django

# Agregar el path del proyecto
sys.path.append('c:/catalog_pos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from django.urls import reverse, resolve
from django.test import RequestFactory
from rest_framework.test import APIRequestFactory
from pedidos_avanzados.viewsets import OrdenClienteViewSet

def test_urls():
    """Test para verificar las URLs de pedidos avanzados"""
    print("=== VERIFICACIÓN DE URLs PEDIDOS AVANZADOS ===\n")
    
    # URLs del API que deberían estar disponibles
    api_urls = [
        '/api/pedidos-avanzados/ordenes-cliente/',
        '/api/pedidos-avanzados/seguimiento-productos/',
        '/api/pedidos-avanzados/entregas-parciales/',
        '/api/pedidos-avanzados/notas-credito/',
        '/api/pedidos-avanzados/portal-politicas/',
        '/api/pedidos-avanzados/productos-compartir/',
    ]
    
    factory = APIRequestFactory()
    
    for url in api_urls:
        try:
            # Resolver la URL
            resolved = resolve(url)
            print(f"✅ URL válida: {url}")
            print(f"   View: {resolved.func.cls.__name__}")
            print(f"   App: {resolved.app_name}")
            print(f"   Namespace: {resolved.namespace}")
            print()
        except Exception as e:
            print(f"❌ Error en URL: {url}")
            print(f"   Error: {str(e)}")
            print()
    
    # Test de actions específicas
    print("=== VERIFICACIÓN DE ACTIONS ESPECÍFICAS ===\n")
    
    action_urls = [
        '/api/pedidos-avanzados/ordenes-cliente/crear_desde_pedidos/',
        '/api/pedidos-avanzados/ordenes-cliente/pendientes/',
        '/api/pedidos-avanzados/entregas-parciales/procesar_entrega/',
        '/api/pedidos-avanzados/productos-compartir/registrar_compartido/',
    ]
    
    for url in action_urls:
        try:
            resolved = resolve(url)
            print(f"✅ Action válida: {url}")
            print(f"   View: {resolved.func.cls.__name__}")
            print()
        except Exception as e:
            print(f"❌ Error en action: {url}")
            print(f"   Error: {str(e)}")
            print()
    
    print("=== VERIFICACIÓN COMPLETADA ===")

if __name__ == '__main__':
    test_urls()
