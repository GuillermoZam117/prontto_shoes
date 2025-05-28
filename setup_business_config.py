#!/usr/bin/env python3
"""
Create initial business configuration
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from configuracion.models import ConfiguracionNegocio

def create_initial_config():
    """Create or update initial business configuration"""
    try:
        config = ConfiguracionNegocio.get_configuracion()
        
        # Update with Pronto Shoes branding
        config.nombre_negocio = "Pronto Shoes"
        config.eslogan = "Tu tienda de calzado de confianza"
        config.logo_texto = "Pronto Shoes"
        config.color_primario = "#0d6efd"
        config.color_secundario = "#6c757d"
        config.sidebar_theme = "dark"
        config.sidebar_collapsed_default = False
        config.moneda = "MXN"
        config.simbolo_moneda = "$"
        config.idioma = "es"
        config.timezone = "America/Mexico_City"
        
        config.save()
        
        print("✓ Business configuration created/updated successfully!")
        print(f"Business Name: {config.nombre_negocio}")
        print(f"Slogan: {config.eslogan}")
        print(f"Logo Text: {config.logo_texto}")
        print(f"Primary Color: {config.color_primario}")
        print(f"Currency: {config.simbolo_moneda} {config.moneda}")
        
    except Exception as e:
        print(f"Error creating configuration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_initial_config()
