#!/usr/bin/env python
"""
Test script to verify auto-display functionality in reports
"""
import os
import sys
import django

# Configure Django first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

# Now import Django modules
from django.test import RequestFactory
from django.contrib.auth.models import User

from reportes.views import ejecutar_reporte

def test_auto_display():
    """Test that reports auto-execute and display data on page load"""
    print("=== TESTING AUTO-DISPLAY FUNCTIONALITY ===")
    
    # Create a test request
    factory = RequestFactory()
    
    # Create or get a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
    )
    
    # Test different report types
    report_types = [
        'clientes_inactivos',
        'historial_precios',
        'inventario_diario',
        'productos_mas_vendidos'
    ]
    
    for report_type in report_types:
        print(f"\n--- Testing {report_type} ---")
        
        try:
            # Create GET request (simulating page load)
            request = factory.get(f'/reportes/ejecutar/{report_type}/')
            request.user = user
            
            # Call the view
            response = ejecutar_reporte(request, report_type)
            
            # Check if response contains auto-generated data
            if hasattr(response, 'context_data'):
                context = response.context_data
                if 'datos_reporte' in context and context['datos_reporte']:
                    print(f"✅ {report_type}: Auto-execution successful")
                    datos = context['datos_reporte']
                    print(f"   - Data type: {type(datos)}")
                    if isinstance(datos, dict):
                        print(f"   - Keys: {list(datos.keys())}")
                        if 'datos' in datos:
                            print(f"   - Records: {len(datos['datos'])}")
                        if 'resumen' in datos:
                            print(f"   - Summary: {datos['resumen']}")
                else:
                    print(f"❌ {report_type}: No auto-generated data found")
            else:
                print(f"⚠️  {report_type}: Response has no context data")
                
        except Exception as e:
            print(f"❌ {report_type}: Error - {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_auto_display()
