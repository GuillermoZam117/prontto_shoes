#!/usr/bin/env python
"""
Simple test for tendencias_ventas report fix
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

try:
    from reportes.views import ReportesAvanzadosAPIView
    from datetime import datetime, timedelta
    
    print("Testing tendencias_ventas report fix...")
    
    view = ReportesAvanzadosAPIView()
    parametros = {
        'fecha_desde': datetime.now() - timedelta(days=30),
        'fecha_hasta': datetime.now(),
        'limite': 100
    }
    
    resultado = view._generar_reporte_tendencias_ventas(parametros)
    
    print("✅ Report generated successfully!")
    print(f"📈 Total records: {len(resultado.get('datos', []))}")
    print(f"🔍 Summary: {resultado.get('resumen', {})}")
    
    if resultado.get('datos'):
        print(f"📄 Sample data: {resultado['datos'][0]}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
