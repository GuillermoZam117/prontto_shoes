#!/usr/bin/env python
"""
Complete Sidebar and Configuration Testing Script
Tests all aspects of the sidebar interface and business configuration system
"""
import os
import sys
import django
import requests
import json
from pathlib import Path

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
sys.path.append(str(Path(__file__).parent))
django.setup()

from django.contrib.auth.models import User
from configuracion.models import ConfiguracionNegocio


def test_configuration_api():
    """Test the configuration API endpoints"""
    print("🔧 Testing Configuration API Endpoints...")
    
    base_url = "http://127.0.0.1:8000"
    
    # Test public configuration endpoint
    try:
        response = requests.get(f"{base_url}/api/configuracion/publica/")
        if response.status_code == 200:
            config_data = response.json()
            print(f"✅ Public Configuration API: {response.status_code}")
            print(f"   - Business Name: {config_data.get('nombre_negocio', 'N/A')}")
            print(f"   - Primary Color: {config_data.get('color_primario', 'N/A')}")
            print(f"   - Theme: {config_data.get('sidebar_theme', 'N/A')}")
        else:
            print(f"❌ Public Configuration API failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Public Configuration API error: {e}")


def test_business_configuration():
    """Test business configuration model"""
    print("\n🏢 Testing Business Configuration Model...")
    
    try:
        config = ConfiguracionNegocio.get_configuracion()
        print(f"✅ Configuration loaded successfully")
        print(f"   - Business Name: {config.nombre_negocio}")
        print(f"   - Logo Text: {config.logo_texto}")
        print(f"   - Primary Color: {config.color_primario}")
        print(f"   - Secondary Color: {config.color_secundario}")
        print(f"   - Sidebar Theme: {config.sidebar_theme}")
        print(f"   - Sidebar Collapsed: {config.sidebar_collapsed_default}")
        print(f"   - Currency: {config.moneda} ({config.simbolo_moneda})")
        print(f"   - Language: {config.idioma}")
        
        # Test configuration update
        original_slogan = config.eslogan
        config.eslogan = "Test Slogan Update"
        config.save()
        
        # Reload and verify
        config_reloaded = ConfiguracionNegocio.get_configuracion()
        if config_reloaded.eslogan == "Test Slogan Update":
            print("✅ Configuration update successful")
            
            # Restore original
            config_reloaded.eslogan = original_slogan
            config_reloaded.save()
            print("✅ Configuration restored")
        else:
            print("❌ Configuration update failed")
            
    except Exception as e:
        print(f"❌ Business Configuration error: {e}")


def test_sidebar_features():
    """Test sidebar specific features"""
    print("\n📋 Testing Sidebar Features...")
    
    try:
        config = ConfiguracionNegocio.get_configuracion()
        
        # Test theme options
        available_themes = ['light', 'dark', 'blue', 'green']
        print(f"✅ Current theme: {config.sidebar_theme}")
        print(f"✅ Available themes: {', '.join(available_themes)}")
        
        # Test color customization
        print(f"✅ Primary color: {config.color_primario}")
        print(f"✅ Secondary color: {config.color_secundario}")
        
        # Test collapse state
        print(f"✅ Default collapsed state: {config.sidebar_collapsed_default}")
        
        print("✅ All sidebar features accessible")
        
    except Exception as e:
        print(f"❌ Sidebar features error: {e}")


def test_urls_and_views():
    """Test URL configuration and view accessibility"""
    print("\n🌐 Testing URLs and Views...")
    
    base_url = "http://127.0.0.1:8000"
    
    # Test key URLs
    test_urls = [
        ("/sidebar-demo/", "Sidebar Demo"),
        ("/api/configuracion/publica/", "Public Configuration API"),
    ]
    
    for url, description in test_urls:
        try:
            response = requests.get(f"{base_url}{url}")
            if response.status_code == 200:
                print(f"✅ {description}: {response.status_code}")
            elif response.status_code == 302:
                print(f"🔄 {description}: {response.status_code} (Redirect)")
            else:
                print(f"❌ {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ {description} error: {e}")


def test_static_files():
    """Test static file accessibility"""
    print("\n📁 Testing Static Files...")
    
    static_files = [
        "frontend/static/css/sidebar.css",
        "frontend/static/js/sidebar.js",
        "frontend/static/images/logo-placeholder.svg",
        "frontend/static/images/logo-placeholder.png",
    ]
    
    for file_path in static_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} not found")


def test_template_files():
    """Test template file existence"""
    print("\n📄 Testing Template Files...")
    
    template_files = [
        "frontend/templates/layouts/base.html",
        "frontend/templates/components/navigation/sidebar.html",
        "frontend/templates/components/navigation/sidebar_nav.html",
        "frontend/templates/sidebar_demo.html",
        "frontend/templates/configuracion/management.html",
    ]
    
    for file_path in template_files:
        full_path = Path(__file__).parent / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} not found")


def create_test_user():
    """Create a test user for authentication testing"""
    print("\n👤 Setting up Test User...")
    
    try:
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@prontoshoes.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            user.set_password('admin123')
            user.save()
            print("✅ Test user created: admin/admin123")
        else:
            print("✅ Test user already exists: admin")
            
        return user
    except Exception as e:
        print(f"❌ User creation error: {e}")
        return None


def main():
    """Run all tests"""
    print("🧪 Starting Complete Sidebar and Configuration Tests...")
    print("=" * 60)
    
    # Create test user
    create_test_user()
    
    # Run all tests
    test_business_configuration()
    test_configuration_api()
    test_sidebar_features()
    test_urls_and_views()
    test_static_files()
    test_template_files()
    
    print("\n" + "=" * 60)
    print("🎉 Testing Complete!")
    print("\nNext Steps:")
    print("1. Visit http://127.0.0.1:8000/sidebar-demo/ to test sidebar functionality")
    print("2. Login with admin/admin123 to access configuration management")
    print("3. Visit http://127.0.0.1:8000/configuracion/gestion/ for config management")
    print("4. Test mobile responsiveness and keyboard shortcuts")
    print("5. Verify logo upload and theme changes")


if __name__ == "__main__":
    main()
