import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from django.utils import timezone
from reportes.views import ReportesAvanzadosAPIView
from datetime import datetime, timedelta

print("=== TESTING REPORTES AVANZADOS ===")

try:
    vista = ReportesAvanzadosAPIView()
    print("Vista creada exitosamente")
    
    # Test 1: Clientes inactivos
    print("\n1. Testing clientes inactivos...")
    parametros = {
        'fecha_desde': '2024-01-01',
        'fecha_hasta': '2025-12-31',
        'limite_registros': 100,
        'dias_inactividad': 30
    }
    
    resultado = vista._generar_reporte_clientes_inactivos(parametros)
    print(f"Resultado: {type(resultado)}")
    
    if isinstance(resultado, dict) and 'datos' in resultado:
        datos = resultado['datos']
        print(f"Registros encontrados: {len(datos)}")
        if datos:
            print(f"Primer registro: {datos[0]}")
    
    # Test 2: Historial de precios
    print("\n2. Testing historial precios...")
    parametros2 = {
        'fecha_desde': '2024-01-01',
        'fecha_hasta': '2025-12-31',
        'producto_id': None,
        'limite_registros': 100
    }
    
    resultado2 = vista._generar_reporte_historial_precios(parametros2)
    print(f"Resultado: {type(resultado2)}")
    
    if isinstance(resultado2, dict) and 'datos' in resultado2:
        datos2 = resultado2['datos']
        print(f"Registros encontrados: {len(datos2)}")
        if datos2:
            print(f"Primer registro: {datos2[0]}")
    
    print("\nTESTS COMPLETADOS EXITOSAMENTE")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
