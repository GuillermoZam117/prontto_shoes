#!/usr/bin/env python
"""
Simple verification test for auto-display functionality
"""
import os
import sys
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from reportes.views import ejecutar_reporte
from django.http import HttpRequest
from django.contrib.auth.models import User

def test_auto_execution():
    """Test that reports auto-execute when accessed with GET request"""
    print("=== TESTING AUTO-EXECUTION FUNCTIONALITY ===")
    
    # Create a test user
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
            # Create a mock GET request
            request = HttpRequest()
            request.method = 'GET'
            request.user = user
            request.META = {'REQUEST_METHOD': 'GET'}
            
            # Call the view directly
            response = ejecutar_reporte(request, report_type)
            
            if response.status_code == 200:
                print(f"✅ {report_type}: View executed successfully (Status: {response.status_code})")
                
                # Check if response contains auto-generated content
                content = response.content.decode('utf-8')
                
                # Look for indicators that auto-execution worked
                checks = [
                    ('Auto-generado', 'Auto-generated badge'),
                    ('datos-reporte', 'Report data script'),
                    ('Resultados del Reporte', 'Results section'),
                    ('resumenSection', 'Summary section'),
                    ('tablaResultados', 'Results table'),
                    ('metadatosSection', 'Metadata section')
                ]
                
                found_count = 0
                for check_string, description in checks:
                    if check_string in content:
                        print(f"   ✅ {description} found")
                        found_count += 1
                    else:
                        print(f"   ❌ {description} not found")
                
                if found_count >= 3:
                    print(f"   🎉 Auto-display working! Found {found_count}/6 indicators")
                else:
                    print(f"   ⚠️  Partial functionality: Found {found_count}/6 indicators")
                    
            else:
                print(f"❌ {report_type}: Failed (Status: {response.status_code})")
                
        except Exception as e:
            print(f"❌ {report_type}: Error - {str(e)}")

    print("\n=== VERIFICATION COMPLETED ===")
    print("\n🌐 Server running at: http://127.0.0.1:8000/")
    print("📊 Test reports at: http://127.0.0.1:8000/reportes/dashboard/")

if __name__ == "__main__":
    test_auto_execution()
