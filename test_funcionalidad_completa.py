#!/usr/bin/env python3
"""
Verificación específica de funcionalidad del sidebar y elementos interactivos
"""
import requests
from bs4 import BeautifulSoup
import re

def test_sidebar_functionality():
    """Probar elementos específicos del sidebar"""
    print("🔍 PROBANDO FUNCIONALIDAD DEL SIDEBAR")
    print("=" * 50)
    
    try:
        response = requests.get("http://127.0.0.1:8000", timeout=10)
        if response.status_code != 200:
            print(f"❌ Error del servidor: {response.status_code}")
            return False
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Verificar elementos del sidebar
        sidebar_tests = [
            ("Sidebar Container", "#posSidebar"),
            ("Toggle Button", "#sidebarToggle"),
            ("Main Content", "#mainContent"),
            ("Dashboard Link", "a[href*='dashboard']"),
            ("Sales Navigation", "a[href*='sales'], a[href*='venta']"),
            ("Products Navigation", "a[href*='product'], a[href*='producto']"),
            ("Reports Navigation", "a[href*='report'], a[href*='reporte']"),
        ]
        
        print("📋 Elementos del Sidebar:")
        for test_name, selector in sidebar_tests:
            element = soup.select_one(selector)
            if element:
                print(f"  ✅ {test_name} - ENCONTRADO")
                if element.get('class'):
                    print(f"     Clases: {' '.join(element.get('class'))}")
            else:
                print(f"  ❌ {test_name} - NO ENCONTRADO")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al probar sidebar: {e}")
        return False

def test_dashboard_elements():
    """Probar elementos específicos del dashboard"""
    print("\n📊 PROBANDO ELEMENTOS DEL DASHBOARD")
    print("=" * 50)
    
    try:
        response = requests.get("http://127.0.0.1:8000", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Verificar estadísticas
        stats_cards = soup.select('.statistics-card, .stat-card, .card')
        print(f"📈 Tarjetas de estadísticas encontradas: {len(stats_cards)}")
        
        # Verificar gráficos
        chart_elements = soup.select('canvas, #salesChart, [id*="chart"]')
        print(f"📊 Elementos de gráficos encontrados: {len(chart_elements)}")
        
        # Verificar botones de acción rápida
        action_buttons = soup.select('.quick-action, .btn, button')
        print(f"🔘 Botones de acción encontrados: {len(action_buttons)}")
        
        # Verificar tablas de datos
        tables = soup.select('table, .table')
        print(f"📋 Tablas de datos encontradas: {len(tables)}")
        
        # Verificar scripts JavaScript
        scripts = soup.select('script')
        js_features = []
        
        for script in scripts:
            if script.string:
                content = script.string
                if 'Chart' in content:
                    js_features.append("Chart.js")
                if 'bootstrap' in content.lower():
                    js_features.append("Bootstrap JS")
                if 'sidebar' in content.lower():
                    js_features.append("Sidebar JS")
        
        print(f"🔧 Funcionalidades JS detectadas: {', '.join(js_features) if js_features else 'Ninguna'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al probar dashboard: {e}")
        return False

def test_responsive_design():
    """Probar elementos de diseño responsivo"""
    print("\n📱 PROBANDO DISEÑO RESPONSIVO")
    print("=" * 50)
    
    try:
        response = requests.get("http://127.0.0.1:8000", timeout=10)
        content = response.text
        
        # Verificar Bootstrap grid
        grid_classes = ['col-', 'row', 'container']
        found_grid = []
        
        for grid_class in grid_classes:
            if grid_class in content:
                count = content.count(grid_class)
                found_grid.append(f"{grid_class} ({count})")
        
        print(f"🎯 Clases de grid Bootstrap: {', '.join(found_grid)}")
        
        # Verificar viewport meta tag
        soup = BeautifulSoup(content, 'html.parser')
        viewport = soup.select_one('meta[name="viewport"]')
        if viewport:
            print(f"📱 Viewport configurado: {viewport.get('content')}")
        else:
            print("⚠️ Viewport no configurado")
        
        # Verificar media queries en CSS
        css_files = soup.select('link[rel="stylesheet"]')
        print(f"🎨 Archivos CSS enlazados: {len(css_files)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al probar diseño responsivo: {e}")
        return False

def main():
    """Ejecutar todas las pruebas de funcionalidad"""
    print("🚀 PRUEBA COMPLETA DE FUNCIONALIDAD DEL POS")
    print("=" * 60)
    
    # Probar sidebar
    test_sidebar_functionality()
    
    # Probar dashboard
    test_dashboard_elements()
    
    # Probar diseño responsivo
    test_responsive_design()
    
    print("\n" + "=" * 60)
    print("✅ TODAS LAS PRUEBAS COMPLETADAS")
    print("\n💡 SIGUIENTE PASO:")
    print("   Abre http://127.0.0.1:8000 en tu navegador")
    print("   Presiona F12 para abrir DevTools")
    print("   Ve a la pestaña Console para ver logs del sidebar-test.js")
    print("   Prueba hacer clic en el botón de toggle del sidebar")

if __name__ == "__main__":
    main()
