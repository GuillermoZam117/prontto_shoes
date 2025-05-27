#!/usr/bin/env python
"""
Script de prueba para los reportes avanzados del sistema POS
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from reportes.views import ReportesAvanzadosAPIView
from datetime import datetime, timedelta
from django.utils import timezone
import json

def test_reporte_clientes_sin_movimientos():
    """Probar el reporte de clientes sin movimientos"""
    print("=== TESTING REPORTE: CLIENTES SIN MOVIMIENTOS ===")
    
    vista = ReportesAvanzadosAPIView()
    
    parametros = {
        'fecha_desde': '2024-01-01',
        'fecha_hasta': '2025-12-31',
        'incluir_nuevos': True
    }
    
    try:
        generador = vista.generadores_reportes['clientes_sin_movimientos']
        resultado = generador(parametros)
        
        print(f"✅ Ejecutado exitosamente")
        print(f"Registros encontrados: {len(resultado)}")
        
        if resultado:
            print("Muestra de datos:")
            for i, registro in enumerate(resultado[:3]):
                print(f"  {i+1}. Cliente: {registro.get('nombre', 'N/A')} - Último pedido: {registro.get('ultimo_pedido', 'N/A')}")
        else:
            print("No se encontraron clientes sin movimientos")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reporte_historial_precios():
    """Probar el reporte de historial de cambios de precios"""
    print("\n=== TESTING REPORTE: HISTORIAL DE CAMBIOS DE PRECIOS ===")
    
    vista = ReportesAvanzadosAPIView()
    
    parametros = {
        'fecha_desde': '2024-01-01',
        'fecha_hasta': '2025-12-31',
        'producto_id': None  # Todos los productos
    }
    
    try:
        generador = vista.generadores_reportes['historial_cambios_precios']
        resultado = generador(parametros)
        
        print(f"✅ Ejecutado exitosamente")
        print(f"Registros encontrados: {len(resultado)}")
        
        if resultado:
            print("Muestra de datos:")
            for i, registro in enumerate(resultado[:3]):
                print(f"  {i+1}. Producto: {registro.get('producto', 'N/A')} - Precio: {registro.get('precio_nuevo', 'N/A')}")
        else:
            print("No se encontraron cambios de precios")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reporte_inventario_diario():
    """Probar el reporte de inventario diario y traspasos"""
    print("\n=== TESTING REPORTE: INVENTARIO DIARIO Y TRASPASOS ===")
    
    vista = ReportesAvanzadosAPIView()
    
    parametros = {
        'fecha_desde': '2025-05-01',
        'fecha_hasta': '2025-05-31',
        'tienda_id': None  # Todas las tiendas
    }
    
    try:
        generador = vista.generadores_reportes['inventario_diario_traspasos']
        resultado = generador(parametros)
        
        print(f"✅ Ejecutado exitosamente")
        print(f"Registros encontrados: {len(resultado)}")
        
        if resultado:
            print("Muestra de datos:")
            for i, registro in enumerate(resultado[:3]):
                print(f"  {i+1}. Producto: {registro.get('producto', 'N/A')} - Stock: {registro.get('stock_actual', 'N/A')}")
        else:
            print("No se encontraron registros de inventario")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_reportes():
    """Probar todos los generadores de reportes"""
    print("=== TESTING TODOS LOS GENERADORES DE REPORTES ===")
    
    vista = ReportesAvanzadosAPIView()
    print(f"Total de generadores disponibles: {len(vista.generadores_reportes)}")
    
    for nombre in vista.generadores_reportes.keys():
        print(f"  ✓ {nombre}")
    
    print()
    
    # Ejecutar pruebas individuales
    resultados = []
    
    resultados.append(test_reporte_clientes_sin_movimientos())
    resultados.append(test_reporte_historial_precios())
    resultados.append(test_reporte_inventario_diario())
    
    # Resumen final
    print(f"\n=== RESUMEN DE PRUEBAS ===")
    exitosos = sum(resultados)
    total = len(resultados)
    print(f"Pruebas exitosas: {exitosos}/{total}")
    
    if exitosos == total:
        print("🎉 TODAS LAS PRUEBAS PASARON")
    else:
        print("⚠️ ALGUNAS PRUEBAS FALLARON")

if __name__ == "__main__":
    test_all_reportes()
