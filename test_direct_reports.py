#!/usr/bin/env python
"""
Direct test script for remaining 7 report generators in Django POS system
Tests report methods directly without API authentication issues
"""

import os
import django
from datetime import datetime, timedelta
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from reportes.views import ReportesAvanzadosAPIView
from django.contrib.auth import get_user_model

def test_report_method_directly(tipo_reporte, parametros=None):
    """Test a report method directly by calling the internal method"""
    print(f"\n{'='*60}")
    print(f"TESTING REPORT: {tipo_reporte}")
    print(f"{'='*60}")
    
    try:
        # Create view instance
        view = ReportesAvanzadosAPIView()
        
        # Default parameters
        default_params = {
            'fecha_desde': datetime.now() - timedelta(days=30),
            'fecha_hasta': datetime.now(),
            'limite': 100
        }
        
        if parametros:
            default_params.update(parametros)
        
        # Get the appropriate method
        method_map = {
            'descuentos_mensuales': '_generar_reporte_descuentos_mensuales',
            'cumplimiento_metas': '_generar_reporte_cumplimiento_metas', 
            'ventas_por_vendedor': '_generar_reporte_ventas_vendedor',
            'productos_mas_vendidos': '_generar_reporte_productos_vendidos',
            'analisis_rentabilidad': '_generar_reporte_rentabilidad',
            'stock_critico': '_generar_reporte_stock_critico',
            'tendencias_ventas': '_generar_reporte_tendencias_ventas'
        }
        
        method_name = method_map.get(tipo_reporte)
        if not method_name:
            print(f"❌ Error: No method found for report type '{tipo_reporte}'")
            return False
            
        # Get the method from the view instance
        if hasattr(view, method_name):
            method = getattr(view, method_name)
            
            print(f"📊 Executing method: {method_name}")
            print(f"📋 Parameters: {default_params}")
            
            # Call the method
            resultado = method(default_params)
            
            # Display results
            print(f"✅ Report generated successfully!")
            print(f"📈 Total records: {len(resultado.get('datos', []))}")
            print(f"🔍 Summary: {resultado.get('resumen', {})}")
            
            # Show first few records if available
            datos = resultado.get('datos', [])
            if datos:
                print(f"\n📄 Sample data (first 3 records):")
                for i, record in enumerate(datos[:3]):
                    print(f"  {i+1}. {record}")
            
            # Test CSV export functionality
            print(f"\n🔄 Testing CSV export...")
            if 'csv_data' in resultado:
                csv_lines = resultado['csv_data'].split('\n')
                print(f"📋 CSV Headers: {csv_lines[0] if csv_lines else 'No headers'}")
                print(f"📊 CSV Lines: {len(csv_lines) - 1}")
            else:
                print("⚠️  No CSV data in result")
            
            return True
            
        else:
            print(f"❌ Error: Method '{method_name}' not found in view")
            return False
            
    except Exception as e:
        print(f"❌ Error executing report: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test all remaining report generators"""
    print("🚀 Testing Remaining Advanced Reports")
    print("=" * 80)
    
    # List of remaining reports to test
    reports_to_test = [
        'descuentos_mensuales',
        'cumplimiento_metas', 
        'ventas_por_vendedor',
        'productos_mas_vendidos',
        'analisis_rentabilidad',
        'stock_critico',
        'tendencias_ventas'
    ]
    
    results = {}
    
    for report_type in reports_to_test:
        success = test_report_method_directly(report_type)
        results[report_type] = success
        
        # Add a small delay between tests
        import time
        time.sleep(1)
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 TESTING SUMMARY")
    print(f"{'='*80}")
    
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"✅ Successful tests: {successful}/{total}")
    print(f"❌ Failed tests: {total - successful}/{total}")
    
    print(f"\n📋 Detailed Results:")
    for report_type, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {report_type}: {status}")
    
    if successful == total:
        print(f"\n🎉 ALL TESTS PASSED! Advanced reports module is ready.")
    else:
        print(f"\n⚠️  Some tests failed. Please review the errors above.")

if __name__ == "__main__":
    main()
