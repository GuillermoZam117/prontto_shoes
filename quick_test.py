import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from reportes.views import ReportesAvanzadosAPIView
from datetime import datetime, timedelta

view = ReportesAvanzadosAPIView()
parametros = {
    'fecha_desde': datetime.now() - timedelta(days=30),
    'fecha_hasta': datetime.now(),
    'limite': 100
}

print("Testing tendencias_ventas...")
resultado = view._generar_reporte_tendencias_ventas(parametros)
print("✅ Success!")
print(f"Records: {len(resultado.get('datos', []))}")
print(f"Summary: {resultado.get('resumen', {})}")
