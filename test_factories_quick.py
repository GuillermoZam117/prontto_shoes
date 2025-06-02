#!/usr/bin/env python
"""
Quick test of factories to identify field mismatch issues
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Now test the factories
from tests.factories import *

def test_all_factories():
    print("Testing all factories for field mismatches...")
    
    factories_to_test = [
        ('UserFactory', UserFactory),
        ('TiendaFactory', TiendaFactory),
        ('ProveedorFactory', ProveedorFactory),
        ('ProductoFactory', ProductoFactory),
        ('ClienteFactory', ClienteFactory),
        ('CajaFactory', CajaFactory),
        ('InventarioFactory', InventarioFactory),
        ('DevolucionFactory', DevolucionFactory),
        ('TransaccionCajaFactory', TransaccionCajaFactory),
        ('TabuladorDescuentoFactory', TabuladorDescuentoFactory),
    ]
    
    errors = []
    success = []
    
    for name, factory_class in factories_to_test:
        try:
            print(f"Testing {name}...", end=" ")
            instance = factory_class()
            print("✅ Success")
            success.append(name)
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            errors.append((name, str(e)))
    
    print(f"\n=== RESULTS ===")
    print(f"Successful: {len(success)}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print(f"\n=== ERRORS TO FIX ===")
        for name, error in errors:
            print(f"- {name}: {error}")
    
    return len(errors) == 0

if __name__ == '__main__':
    test_all_factories()
