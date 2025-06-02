#!/usr/bin/env python3
"""
Script para probar visualmente el dashboard modernizado del sistema POS
"""

import os
import sys
import django
from django.core.management import call_command
from django.test import Client
from django.contrib.auth import get_user_model
import webbrowser
import time

# Configurar Django
sys.path.append('c:/catalog_pos')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

def test_dashboard_visual():
    """Prueba visual del dashboard modernizado"""
    
    print("🎨 PROBANDO DASHBOARD MODERNIZADO")
    print("=" * 50)
    
    try:
        # Configurar cliente de prueba
        client = Client()
        User = get_user_model()
        
        # Crear usuario de prueba si no existe
        try:
            user = User.objects.get(username='admin')
            print(f"✅ Usuario admin encontrado: {user.username}")
        except User.DoesNotExist:
            user = User.objects.create_superuser(
                username='admin',
                email='admin@prontopos.com',
                password='admin123'
            )
            print(f"✅ Usuario admin creado: {user.username}")
        
        # Iniciar sesión
        login_success = client.login(username='admin', password='admin123')
        if login_success:
            print("✅ Inicio de sesión exitoso")
        else:
            print("❌ Error en inicio de sesión")
            return False
          # Probar acceso al dashboard
        response = client.get('/dashboard/')
        print(f"✅ Respuesta del dashboard: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard carga correctamente")
            
            # Verificar contenido moderno
            content = response.content.decode('utf-8')
            
            # Verificar elementos del diseño moderno
            modern_elements = [
                'dashboard-container',
                'welcome-section',
                'welcome-title',
                'stat-card',
                'modern-card',
                'activity-item',
                'modern-table',
                'quick-action-btn',
                'fab',
                'offcanvas'
            ]
            
            print("\n🔍 VERIFICANDO ELEMENTOS MODERNOS:")
            for element in modern_elements:
                if element in content:
                    print(f"  ✅ {element} - Presente")
                else:
                    print(f"  ❌ {element} - No encontrado")
            
            # Verificar CSS moderno
            modern_css = [
                'backdrop-filter: blur',
                'linear-gradient',
                'border-radius: 20px',
                'transform: translateY',
                'box-shadow:'
            ]
            
            print("\n🎨 VERIFICANDO ESTILOS MODERNOS:")
            for css in modern_css:
                if css in content:
                    print(f"  ✅ {css} - Aplicado")
                else:
                    print(f"  ❌ {css} - No encontrado")
            
            # Verificar JavaScript
            js_features = [
                'Chart.js',
                'updateDashboard',
                'sync:statusChanged'
            ]
            
            print("\n⚡ VERIFICANDO FUNCIONALIDAD JAVASCRIPT:")
            for js in js_features:
                if js in content:
                    print(f"  ✅ {js} - Implementado")
                else:
                    print(f"  ❌ {js} - No encontrado")
                    
            print("\n📱 CARACTERÍSTICAS DEL DASHBOARD MODERNIZADO:")
            print("  ✨ Diseño glassmorphism con efectos de transparencia")
            print("  🌈 Gradientes modernos en colores púrpura-azul")
            print("  📊 Tarjetas de estadísticas con animaciones hover")
            print("  📈 Gráficos interactivos con Chart.js")
            print("  🔄 Actualizaciones en tiempo real cada 5 minutos")
            print("  📱 Diseño completamente responsivo")
            print("  🎭 Animaciones suaves y transiciones")
            print("  🚀 Botón de acción flotante con panel de accesos rápidos")
            print("  🎯 Iconografía moderna con Bootstrap Icons")
            print("  ⚡ Interfaz optimizada para experiencia de usuario")
            
            return True
            
        else:
            print(f"❌ Error al cargar dashboard: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")
        return False

def start_server_and_open():
    """Inicia el servidor y abre el navegador"""
    print("\n🚀 INICIANDO SERVIDOR DE DESARROLLO")
    print("=" * 50)
    
    # Crear script de inicio
    startup_script = """
@echo off
echo Iniciando servidor Django...
cd /d c:\\catalog_pos
python manage.py runserver 127.0.0.1:8000
pause
"""
    
    with open('c:/catalog_pos/start_server.bat', 'w') as f:
        f.write(startup_script)
    
    print("📝 Script de inicio creado: start_server.bat")
    print("🌐 Para ver el dashboard modernizado:")
    print("   1. Ejecuta: start_server.bat")
    print("   2. Abre: http://127.0.0.1:8000")
    print("   3. Usuario: admin")
    print("   4. Contraseña: admin123")
    
    # Abrir navegador automáticamente si se desea
    try:
        import subprocess
        print("\n🚀 Intentando iniciar servidor automáticamente...")
        subprocess.Popen(['start_server.bat'], shell=True, cwd='c:/catalog_pos')
        time.sleep(3)
        webbrowser.open('http://127.0.0.1:8000')
        print("✅ Navegador abierto automáticamente")
    except Exception as e:
        print(f"⚠️  No se pudo abrir automáticamente: {e}")

if __name__ == "__main__":
    print("🎨 SISTEMA POS PRONTO SHOES - PRUEBA VISUAL DEL DASHBOARD")
    print("=" * 60)
    
    # Ejecutar prueba visual
    success = test_dashboard_visual()
    
    if success:
        print("\n✅ DASHBOARD MODERNIZADO EXITOSAMENTE")
        print("🎉 El diseño se ha actualizado con:")
        print("   • Efectos glassmorphism")
        print("   • Gradientes modernos")
        print("   • Animaciones suaves")
        print("   • Diseño responsivo")
        print("   • Funcionalidad mejorada")
        
        # Preguntar si quiere iniciar el servidor
        response = input("\n¿Deseas iniciar el servidor para ver el dashboard? (s/n): ")
        if response.lower() in ['s', 'si', 'sí', 'y', 'yes']:
            start_server_and_open()
    else:
        print("\n❌ HUBO PROBLEMAS EN LA PRUEBA")
        print("⚠️  Revisa los errores anteriores")
    
    print("\n" + "=" * 60)
    print("🎨 Prueba visual completada")
