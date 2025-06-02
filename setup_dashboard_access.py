#!/usr/bin/env python3
"""
Script para crear usuario de prueba y verificar acceso al dashboard
"""
import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from django.contrib.auth.models import User

def create_test_user():
    """Crear usuario de prueba si no existe"""
    try:
        # Verificar si ya existe
        if User.objects.filter(username='admin').exists():
            print("✅ Usuario 'admin' ya existe")
            return True
        
        # Crear nuevo usuario
        user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        print("✅ Usuario 'admin' creado exitosamente")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        return True
        
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
        return False

def test_login_access():
    """Probar acceso mediante requests"""
    import requests
    from requests.sessions import Session
    
    try:
        # Crear sesión
        session = Session()
        
        # Obtener página de login para el token CSRF
        login_url = "http://127.0.0.1:8000/accounts/login/"
        response = session.get(login_url)
        
        if response.status_code == 200:
            print("✅ Página de login accesible")
            
            # Buscar token CSRF
            csrf_token = None
            if 'csrfmiddlewaretoken' in response.text:
                import re
                csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]*)"', response.text)
                if csrf_match:
                    csrf_token = csrf_match.group(1)
                    print(f"✅ Token CSRF obtenido: {csrf_token[:20]}...")
            
            if csrf_token:
                # Intentar login
                login_data = {
                    'username': 'admin',
                    'password': 'admin123',
                    'csrfmiddlewaretoken': csrf_token
                }
                
                login_response = session.post(login_url, data=login_data)
                
                if login_response.status_code == 302:  # Redirección después del login
                    print("✅ Login exitoso - redirección detectada")
                    
                    # Intentar acceder al dashboard
                    dashboard_response = session.get("http://127.0.0.1:8000/")
                    
                    if dashboard_response.status_code == 200:
                        content = dashboard_response.text
                        print("✅ Dashboard accesible después del login")
                        
                        # Verificar contenido del dashboard
                        if 'dashboard' in content.lower():
                            print("✅ Contenido del dashboard detectado")
                        if 'sidebar' in content.lower():
                            print("✅ Sidebar detectado")
                        if 'statistics' in content.lower():
                            print("✅ Estadísticas detectadas")
                            
                        return True
                else:
                    print(f"⚠️ Login falló - Status: {login_response.status_code}")
            else:
                print("❌ No se pudo obtener token CSRF")
        else:
            print(f"❌ No se puede acceder a la página de login - Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error al probar login: {e}")
    
    return False

def main():
    """Ejecutar configuración completa"""
    print("🚀 CONFIGURACIÓN DE ACCESO AL DASHBOARD")
    print("=" * 50)
    
    # Crear usuario
    if create_test_user():
        print("\n🔐 PROBANDO ACCESO...")
        if test_login_access():
            print("\n✅ CONFIGURACIÓN COMPLETADA")
            print("\n💡 INSTRUCCIONES PARA ACCESO MANUAL:")
            print("   1. Ve a http://127.0.0.1:8000")
            print("   2. Usa las credenciales:")
            print("      Usuario: admin")
            print("      Contraseña: admin123")
            print("   3. Después del login verás el dashboard completo")
        else:
            print("\n⚠️ ACCESO AUTOMÁTICO FALLÓ")
            print("   Intenta el acceso manual con las credenciales:")
            print("      Usuario: admin")
            print("      Contraseña: admin123")
    else:
        print("\n❌ NO SE PUDO CREAR USUARIO")

if __name__ == "__main__":
    main()
