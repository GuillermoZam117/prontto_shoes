import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from django.utils import timezone
from reportes.views import ReportesAvanzadosAPIView
from datetime import datetime, timedelta

print("=== TESTING REPORTES AVANZADOS CORREGIDOS ===")

try:
    vista = ReportesAvanzadosAPIView()
    print("Vista creada exitosamente")
    
    # Test 1: Clientes inactivos con fechas como objetos datetime
    print("\n1. Testing clientes inactivos con fechas correctas...")
    parametros = {
        'fecha_desde': datetime.strptime('2024-01-01', '%Y-%m-%d').date(),
        'fecha_hasta': datetime.strptime('2025-12-31', '%Y-%m-%d').date(),
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
        print(f"Resumen: {resultado.get('resumen', {})}")
    
    # Test 2: Historial de precios
    print("\n2. Testing historial precios...")
    parametros2 = {
        'fecha_desde': datetime.strptime('2024-01-01', '%Y-%m-%d').date(),
        'fecha_hasta': datetime.strptime('2025-12-31', '%Y-%m-%d').date(),
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
    
    # Test 3: Inventario diario
    print("\n3. Testing inventario diario...")
    parametros3 = {
        'fecha_desde': datetime.strptime('2025-05-01', '%Y-%m-%d').date(),
        'fecha_hasta': datetime.strptime('2025-05-31', '%Y-%m-%d').date(),
        'tienda_id': None,
        'limite_registros': 100
    }
    
    resultado3 = vista._generar_reporte_inventario_diario(parametros3)
    print(f"Resultado: {type(resultado3)}")
    
    if isinstance(resultado3, dict) and 'datos' in resultado3:
        datos3 = resultado3['datos']
        print(f"Registros encontrados: {len(datos3)}")
        if datos3:
            print(f"Primer registro: {datos3[0]}")
    
    print("\n=== TODOS LOS TESTS COMPLETADOS EXITOSAMENTE ===")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
