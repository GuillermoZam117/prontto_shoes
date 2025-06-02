#!/usr/bin/env python3
"""
Prueba simple del dashboard - verificación de archivos y contenido
"""
import os
import requests
from pathlib import Path

def test_dashboard_files():
    """Verificar que los archivos del dashboard existen"""
    print("🔍 Verificando archivos del dashboard...")
    
    files_to_check = [
        "frontend/templates/dashboard/index.html",
        "frontend/static/css/critical.css",
        "frontend/static/css/sidebar.css",
        "frontend/static/js/sidebar-test.js",
        "frontend/templates/layouts/base.html"
    ]
    
    for file_path in files_to_check:
        full_path = Path(file_path)
        if full_path.exists():
            print(f"✅ {file_path} - EXISTE")
            # Verificar tamaño del archivo
            size = full_path.stat().st_size
            print(f"   Tamaño: {size} bytes")
        else:
            print(f"❌ {file_path} - NO ENCONTRADO")
    
    return True

def test_server_response():
    """Probar que el servidor responde"""
    print("\n🌐 Probando respuesta del servidor...")
    
    try:
        response = requests.get("http://127.0.0.1:8000", timeout=5)
        print(f"✅ Servidor responde - Status: {response.status_code}")
        
        # Verificar contenido básico
        content = response.text
        if "dashboard" in content.lower():
            print("✅ Contenido del dashboard detectado")
        if "sidebar" in content.lower():
            print("✅ Sidebar detectado en HTML")
        if "chart" in content.lower():
            print("✅ Charts detectados")
        if "bootstrap" in content.lower():
            print("✅ Bootstrap detectado")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor")
        print("   Asegúrate de que Django esté ejecutándose en http://127.0.0.1:8000")
        return False
    except Exception as e:
        print(f"❌ Error al probar servidor: {e}")
        return False

def test_dashboard_content():
    """Verificar contenido específico del dashboard"""
    print("\n📊 Verificando contenido del dashboard...")
    
    dashboard_file = Path("frontend/templates/dashboard/index.html")
    if not dashboard_file.exists():
        print("❌ Archivo dashboard no encontrado")
        return False
    
    content = dashboard_file.read_text(encoding='utf-8')
    
    # Verificar elementos clave
    checks = [
        ("Statistics Cards", "statistics-card" in content or "stat-card" in content),
        ("Sales Chart", "salesChart" in content or "chart" in content.lower()),
        ("Quick Actions", "quick-action" in content or "btn-" in content),
        ("Activity Feed", "activity" in content.lower()),
        ("Bootstrap Grid", "col-" in content),
        ("Modern Design", "backdrop-filter" in content or "glassmorphism" in content),
    ]
    
    for check_name, check_result in checks:
        if check_result:
            print(f"✅ {check_name} - PRESENTE")
        else:
            print(f"⚠️ {check_name} - NO DETECTADO")
    
    return True

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 PRUEBA SIMPLE DEL DASHBOARD POS")
    print("=" * 50)
    
    # Verificar archivos
    test_dashboard_files()
    
    # Probar servidor
    test_server_response()
    
    # Verificar contenido
    test_dashboard_content()
    
    print("\n" + "=" * 50)
    print("✅ PRUEBA COMPLETADA")
    print("\n💡 Para ver el dashboard:")
    print("   1. Asegúrate de que el servidor Django esté ejecutándose")
    print("   2. Abre http://127.0.0.1:8000 en tu navegador")
    print("   3. Presiona F12 para ver la consola del navegador")

if __name__ == "__main__":
    main()
