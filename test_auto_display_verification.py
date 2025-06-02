#!/usr/bin/env python
"""
Verification script to test auto-display functionality in reports
"""
import os
import sys
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

def test_auto_display_functionality():
    """Test that reports auto-execute and display data on page load"""
    print("=== TESTING AUTO-DISPLAY FUNCTIONALITY ===")
    
    # Create Django test client
    client = Client()
    
    # Create or get a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com', 'first_name': 'Test', 'last_name': 'User'}
    )
    
    # Log in the user
    client.force_login(user)
    
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
            # Make GET request to the report page
            response = client.get(f'/reportes/ejecutar/{report_type}/')
            
            # Check if response is successful
            if response.status_code == 200:
                print(f"✅ {report_type}: Page loads successfully (Status: {response.status_code})")
                
                # Check if response contains auto-generated data
                content = response.content.decode('utf-8')
                
                # Look for indicators that auto-execution worked
                if 'datos-reporte' in content:
                    print(f"   ✅ Auto-generated data script found")
                
                if 'Auto-generado' in content:
                    print(f"   ✅ Auto-generated badge found")
                
                if 'Resultados del Reporte' in content:
                    print(f"   ✅ Results section found")
                
                # Check for specific report data indicators
                if 'resumenSection' in content:
                    print(f"   ✅ Summary section present")
                
                if 'tablaResultados' in content:
                    print(f"   ✅ Results table present")
                
                if 'metadatosSection' in content:
                    print(f"   ✅ Metadata section present")
                    
            else:
                print(f"❌ {report_type}: Failed to load (Status: {response.status_code})")
                
        except Exception as e:
            print(f"❌ {report_type}: Error - {str(e)}")

    print("\n=== VERIFICATION COMPLETED ===")

if __name__ == "__main__":
    test_auto_display_functionality()
