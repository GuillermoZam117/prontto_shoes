import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')

try:
    django.setup()
    print("✅ Django configurado correctamente")
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

try:
    from reportes.views import ReportesAvanzadosAPIView
    print("✅ Importación de views exitosa")
    
    vista = ReportesAvanzadosAPIView()
    print(f"✅ Vista creada exitosamente")
    print(f"Generadores disponibles: {len(vista.generadores_reportes)}")
    
    for nombre in vista.generadores_reportes.keys():
        print(f"  - {nombre}")
        
except Exception as e:
    print(f"❌ Error importando views: {e}")
    import traceback
    traceback.print_exc()
