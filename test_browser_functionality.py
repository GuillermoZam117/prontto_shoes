#!/usr/bin/env python3
"""
Test script to verify auto-display functionality in browser
"""
import requests
import sys
from bs4 import BeautifulSoup

def test_auto_display():
    base_url = "http://localhost:8000"
    
    # Test different report types
    reports_to_test = [
        "inventario",
        "ventas", 
        "traspasos"
    ]
    
    print("=== TESTING AUTO-DISPLAY FUNCTIONALITY ===\n")
    
    for report_type in reports_to_test:
        print(f"🔍 Testing {report_type} report...")
        
        try:
            url = f"{base_url}/reportes/ejecutar/{report_type}/"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {report_type}: HTTP 200 OK")
                
                # Parse HTML to check for auto-displayed data
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check if results card is visible (indicating auto-display)
                results_card = soup.find('div', {'id': 'resultadosCard'})
                if results_card and 'style' not in results_card.attrs:
                    print(f"✅ {report_type}: Results card is visible (auto-displayed)")
                    
                    # Check for summary data
                    summary_section = soup.find('div', {'id': 'resumenSection'})
                    if summary_section and summary_section.find('div', class_='card-title'):
                        print(f"✅ {report_type}: Summary data found")
                    else:
                        print(f"⚠️  {report_type}: Summary data not found")
                    
                    # Check for table data
                    table_section = soup.find('div', {'id': 'tablaSection'})
                    if table_section and table_section.find('table'):
                        print(f"✅ {report_type}: Table data found")
                    else:
                        print(f"⚠️  {report_type}: Table data not found")
                    
                    # Check for auto-generated badge
                    auto_badge = soup.find('span', string=lambda text: text and 'Auto-generado' in text)
                    if auto_badge:
                        print(f"✅ {report_type}: Auto-generated badge found")
                    else:
                        print(f"⚠️  {report_type}: Auto-generated badge not found")
                        
                else:
                    print(f"❌ {report_type}: Results card not visible (auto-display may not be working)")
                    
            else:
                print(f"❌ {report_type}: HTTP {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {report_type}: Connection error - {e}")
        except Exception as e:
            print(f"❌ {report_type}: Unexpected error - {e}")
            
        print()

if __name__ == "__main__":
    test_auto_display()
