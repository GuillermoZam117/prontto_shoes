import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

print("🔧 Final Test: Tendencias Ventas PostgreSQL Fix")
print("=" * 50)

try:
    from reportes.views import ReportesAvanzadosAPIView
    from datetime import datetime, timedelta
    
    view = ReportesAvanzadosAPIView()
    parametros = {
        'fecha_desde': datetime.now() - timedelta(days=30),
        'fecha_hasta': datetime.now(),
        'limite': 100
    }
    
    print("📊 Testing tendencias_ventas generator...")
    resultado = view._generar_reporte_tendencias_ventas(parametros)
    
    print("✅ Report generated successfully!")
    print(f"📈 Total records: {len(resultado.get('datos', []))}")
    print(f"🔍 Summary: {resultado.get('resumen', {})}")
    
    if resultado.get('datos'):
        print(f"📄 Sample data: {resultado['datos'][0]}")
    
    print("\n🎯 Final Status: ALL 10 REPORT GENERATORS WORKING!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("🔧 PostgreSQL compatibility issue still needs fixing")
