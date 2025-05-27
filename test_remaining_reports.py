#!/usr/bin/env python
"""
Test script for remaining 7 report generators in Django POS system
Tests: descuentos_mensuales, cumplimiento_metas, ventas_por_vendedor, 
       productos_mas_vendidos, analisis_rentabilidad, stock_critico, tendencias_ventas
"""

import os
import django
from datetime import datetime, timedelta
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from reportes.models import ReportePersonalizado
from reportes.views import ReportePersonalizadoViewSet

def test_report_generator(tipo_reporte, parametros=None):
    """Test a specific report generator"""
    print(f"\n{'='*60}")
    print(f"TESTING REPORT: {tipo_reporte}")
    print(f"{'='*60}")
    
    try:        # Create report instance
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.first()  # Get first available user
        
        reporte = ReportePersonalizado.objects.create(
            nombre=f"Test {tipo_reporte}",
            tipo=tipo_reporte,
            parametros=parametros or {},
            creado_por=user
        )
          # Initialize API view instance
        from reportes.views import ReportesAvanzadosAPIView
        from rest_framework.test import APIRequestFactory
        
        view = ReportesAvanzadosAPIView()
        factory = APIRequestFactory()
          # Create mock request with parameters
        query_params = {'tipo_reporte': tipo_reporte}
        if parametros:
            query_params.update(parametros)
        
        request = factory.get('/', query_params)
        request.user = user
        
        # Execute report via API
        response = view.get(request)
        
        print(f"✅ Report executed successfully!")
        print(f"📊 Status code: {response.status_code}")
        
        if hasattr(response, 'data') and response.data:
            resultado = response.data
            print(f"📊 Data structure: {type(resultado)}")
            
            if isinstance(resultado, dict):
                print(f"📋 Keys: {list(resultado.keys())}")
                if 'datos' in resultado:
                    data = resultado['datos']
                    print(f"📈 Data count: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                    if data and len(data) > 0:
                        print(f"📝 Sample record: {data[0] if isinstance(data, list) else str(data)[:200]}")
                if 'metadata' in resultado:
                    print(f"🔍 Metadata: {resultado['metadata']}")
            else:
                print(f"📄 Result preview: {str(resultado)[:200]}")
        else:
            print(f"⚠️  No data returned or response error")
            if hasattr(response, 'data'):
                print(f"🔍 Response data: {response.data}")
        
        # Clean up
        reporte.delete()
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error testing {tipo_reporte}: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        return False

def main():
    """Test all remaining report generators"""
    print("🚀 Starting comprehensive report generator testing...")
    
    # Test parameters for different report types
    fecha_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    
    reports_to_test = [
        {
            'tipo': 'descuentos_mensuales',
            'params': {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'filtro_tienda': None
            }
        },
        {
            'tipo': 'cumplimiento_metas',
            'params': {
                'mes': datetime.now().month,
                'año': datetime.now().year,
                'filtro_vendedor': None
            }
        },
        {
            'tipo': 'ventas_por_vendedor',
            'params': {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'filtro_tienda': None
            }
        },
        {
            'tipo': 'productos_mas_vendidos',
            'params': {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'limite': 20,
                'filtro_categoria': None
            }
        },
        {
            'tipo': 'analisis_rentabilidad',
            'params': {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'filtro_producto': None
            }
        },
        {
            'tipo': 'stock_critico',
            'params': {
                'umbral_minimo': 10,
                'filtro_tienda': None,
                'incluir_agotados': True
            }
        },
        {
            'tipo': 'tendencias_ventas',
            'params': {
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin,
                'agrupacion': 'semanal',
                'filtro_categoria': None
            }
        }
    ]
    
    results = {}
    total_tests = len(reports_to_test)
    passed_tests = 0
    
    for report_config in reports_to_test:
        tipo = report_config['tipo']
        params = report_config['params']
        
        success = test_report_generator(tipo, params)
        results[tipo] = success
        if success:
            passed_tests += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"📊 Total tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}")
    print(f"📈 Success rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for tipo, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {tipo}: {status}")
    
    return results

if __name__ == '__main__':
    main()
