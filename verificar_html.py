#!/usr/bin/env python3
"""
Verificar contenido HTML específico del dashboard
"""
import requests

def get_html_content():
    """Obtener y mostrar contenido HTML relevante"""
    try:
        response = requests.get("http://127.0.0.1:8000", timeout=10)
        if response.status_code == 200:
            content = response.text
            
            print("🔍 CONTENIDO HTML ENCONTRADO:")
            print("=" * 50)
            
            # Buscar elementos específicos
            if "sidebar" in content.lower():
                print("✅ 'sidebar' encontrado en HTML")
                
                # Extraer líneas que contienen sidebar
                lines = content.split('\n')
                sidebar_lines = [line.strip() for line in lines if 'sidebar' in line.lower()]
                
                print("\n📋 Líneas con 'sidebar':")
                for i, line in enumerate(sidebar_lines[:10]):  # Mostrar solo las primeras 10
                    print(f"  {i+1}: {line}")
            else:
                print("❌ 'sidebar' NO encontrado en HTML")
            
            # Verificar elementos del dashboard
            dashboard_elements = [
                ("posSidebar", "id=\"posSidebar\""),
                ("sidebarToggle", "id=\"sidebarToggle\""),
                ("mainContent", "id=\"mainContent\""),
                ("statistics-card", "statistics-card"),
                ("salesChart", "salesChart"),
                ("Chart.js", "chart.js"),
                ("Bootstrap", "bootstrap")
            ]
            
            print(f"\n📊 ELEMENTOS DEL DASHBOARD:")
            for element_name, search_term in dashboard_elements:
                if search_term.lower() in content.lower():
                    print(f"  ✅ {element_name} - PRESENTE")
                else:
                    print(f"  ❌ {element_name} - NO ENCONTRADO")
            
            # Mostrar estructura básica
            print(f"\n📏 ESTADÍSTICAS DEL HTML:")
            print(f"  Total de caracteres: {len(content)}")
            print(f"  Total de líneas: {len(content.split('\n'))}")
            
            # Mostrar primeras líneas del body
            if "<body" in content:
                body_start = content.find("<body")
                body_section = content[body_start:body_start+1000]
                print(f"\n🏗️ INICIO DEL BODY:")
                print(body_section[:500] + "..." if len(body_section) > 500 else body_section)
            
        else:
            print(f"❌ Error del servidor: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error al obtener HTML: {e}")

if __name__ == "__main__":
    get_html_content()
