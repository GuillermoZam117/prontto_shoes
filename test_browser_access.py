#!/usr/bin/env python
"""
Quick test to verify the auto-display functionality
"""
import os
import sys
import django
import requests

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

def test_browser_access():
    """Test accessing reports through browser"""
    print("=== TESTING BROWSER ACCESS ===")
    
    base_url = "http://127.0.0.1:8000"
    
    # Test reports that should auto-execute
    reports = [
        'inventario_diario',  # This one worked in the previous test
    ]
    
    for report in reports:
        print(f"\n--- Testing {report} ---")
        url = f"{base_url}/reportes/ejecutar/{report}/"
        
        try:
            response = requests.get(url, timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                
                # Check for key indicators
                indicators = [
                    ('datos-reporte', 'Pre-loaded data script'),
                    ('resultadosCard', 'Results card'),
                    ('tablaResultados', 'Results table'),
                    ('Auto-generado', 'Auto-generated badge'),
                ]
                
                print("Checking for auto-display indicators:")
                for indicator, description in indicators:
                    if indicator in content:
                        print(f"  ✅ {description}")
                    else:
                        print(f"  ❌ {description}")
                        
                # Check if template rendered without errors
                if 'TemplateSyntaxError' in content:
                    print(f"  ❌ Template syntax error detected")
                else:
                    print(f"  ✅ Template rendered without syntax errors")
                    
            else:
                print(f"❌ Failed to access: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

    print(f"\n🌐 Dashboard: {base_url}/reportes/dashboard/")
    print(f"📊 Direct test: {base_url}/reportes/ejecutar/inventario_diario/")

if __name__ == "__main__":
    test_browser_access()
