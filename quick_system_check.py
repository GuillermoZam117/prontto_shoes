#!/usr/bin/env python
"""
VERIFICACIÓN RÁPIDA DEL SISTEMA POS
===================================
"""

import requests
from datetime import datetime

def test_system():
    """Prueba rápida del sistema"""
    
    print("🔍 VERIFICANDO SISTEMA POS PRONTO SHOES")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%d de %B, %Y - %H:%M hrs')}")
    print()
      modules = {
        'Sistema Principal': 'http://127.0.0.1:8000/',
        'Clientes': 'http://127.0.0.1:8000/clientes/',
        'Productos': 'http://127.0.0.1:8000/productos/',
        'Pedidos/POS': 'http://127.0.0.1:8000/ventas/',
        'Reportes': 'http://127.0.0.1:8000/reportes/',
    }
    
    operational_count = 0
    
    for name, url in modules.items():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 302, 403]:
                print(f"✅ {name}: OPERATIVO (Código {response.status_code})")
                operational_count += 1
            else:
                print(f"⚠️ {name}: Código {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: ERROR - {str(e)[:30]}...")
    
    print(f"\n📊 RESUMEN:")
    print(f"   • Módulos operativos: {operational_count}/{len(modules)}")
    print(f"   • Disponibilidad: {(operational_count/len(modules)*100):.0f}%")
    print(f"   • Estado general: {'✅ SISTEMA FUNCIONAL' if operational_count >= 4 else '⚠️ REVISAR SISTEMA'}")
    
    return operational_count >= 4

if __name__ == "__main__":
    system_ok = test_system()
    if system_ok:
        print(f"\n🎉 SISTEMA POS LISTO PARA DEMOSTRACIÓN")
        print(f"🌐 Acceso: http://127.0.0.1:8000/")
    else:
        print(f"\n⚠️ SISTEMA REQUIERE VERIFICACIÓN")
