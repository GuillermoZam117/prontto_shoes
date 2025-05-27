#!/usr/bin/env python3
# Test directo de los reportes avanzados

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

# Importar lo necesario
from django.utils import timezone
from reportes.views import ReportesAvanzadosAPIView
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import User

def test_reporte_directo():
    """Probar reporte directamente sin API"""
    print("=== PRUEBA DIRECTA DE REPORTES ===")
    
    try:
        vista = ReportesAvanzadosAPIView()
        print("✅ Vista creada exitosamente")
        
        # Parámetros para el reporte de clientes inactivos
        parametros = {
            'fecha_desde': '2024-01-01',
            'fecha_hasta': '2025-12-31',
            'limite_registros': 100,
            'dias_inactividad': 30
        }
        
        print("🔄 Ejecutando reporte de clientes inactivos...")
        resultado = vista._generar_reporte_clientes_inactivos(parametros)
        
        print(f"✅ Reporte ejecutado exitosamente")
        print(f"Datos obtenidos: {type(resultado)}")
        print(f"Claves en resultado: {resultado.keys() if isinstance(resultado, dict) else 'No es dict'}")
        
        if isinstance(resultado, dict) and 'datos' in resultado:
            datos = resultado['datos']
            print(f"Número de registros: {len(datos)}")
            
            if datos:
                print("\nPrimeros 3 registros:")
                for i, registro in enumerate(datos[:3]):
                    print(f"  {i+1}. {registro}")
            else:
                print("No se encontraron clientes inactivos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reporte_historial_precios():
    """Probar reporte de historial de precios"""
    print("\n=== PRUEBA REPORTE HISTORIAL DE PRECIOS ===")
    
    try:
        vista = ReportesAvanzadosAPIView()
        
        parametros = {
            'fecha_desde': '2024-01-01',
            'fecha_hasta': '2025-12-31',
            'producto_id': None,
            'limite_registros': 100
        }
        
        print("🔄 Ejecutando reporte de historial de precios...")
        resultado = vista._generar_reporte_historial_precios(parametros)
        
        print(f"✅ Reporte ejecutado exitosamente")
        
        if isinstance(resultado, dict) and 'datos' in resultado:
            datos = resultado['datos']
            print(f"Número de registros: {len(datos)}")
            
            if datos:
                print("\nPrimeros 3 registros:")
                for i, registro in enumerate(datos[:3]):
                    print(f"  {i+1}. {registro}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reporte_inventario():
    """Probar reporte de inventario diario"""
    print("\n=== PRUEBA REPORTE INVENTARIO DIARIO ===")
    
    try:
        vista = ReportesAvanzadosAPIView()
        
        parametros = {
            'fecha_desde': '2025-05-01',
            'fecha_hasta': '2025-05-31',
            'tienda_id': None,
            'limite_registros': 100
        }
        
        print("🔄 Ejecutando reporte de inventario diario...")
        resultado = vista._generar_reporte_inventario_diario(parametros)
        
        print(f"✅ Reporte ejecutado exitosamente")
        
        if isinstance(resultado, dict) and 'datos' in resultado:
            datos = resultado['datos']
            print(f"Número de registros: {len(datos)}")
            
            if datos:
                print("\nPrimeros 3 registros:")
                for i, registro in enumerate(datos[:3]):
                    print(f"  {i+1}. {registro}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Iniciando pruebas de reportes avanzados...")
    
    resultados = []
    resultados.append(test_reporte_directo())
    resultados.append(test_reporte_historial_precios())
    resultados.append(test_reporte_inventario())
    
    exitosos = sum(resultados)
    total = len(resultados)
    
    print(f"\n=== RESUMEN FINAL ===")
    print(f"Pruebas exitosas: {exitosos}/{total}")
    
    if exitosos == total:
        print("🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    else:
        print("⚠️ ALGUNAS PRUEBAS FALLARON")
        
    print("Fin de las pruebas.")
