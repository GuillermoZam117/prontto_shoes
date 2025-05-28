"""
Context processors for the configuracion app
"""
from .models import ConfiguracionNegocio


def business_config(request):
    """
    Context processor to make business configuration available in all templates
    """
    try:
        config = ConfiguracionNegocio.get_configuracion()
        return {
            'business_config': {
                'nombre_negocio': config.nombre_negocio,
                'eslogan': config.eslogan,
                'logo': config.logo.url if config.logo else None,
                'logo_texto': config.logo_texto,
                'sidebar_collapsed_default': config.sidebar_collapsed_default,
                'sidebar_theme': config.sidebar_theme,
                'color_primario': config.color_primario,
                'color_secundario': config.color_secundario,
                'moneda': config.moneda,
                'simbolo_moneda': config.simbolo_moneda,
            }
        }
    except Exception:
        # Return default values if configuration doesn't exist
        return {
            'business_config': {
                'nombre_negocio': 'POS System',
                'eslogan': '',
                'logo': None,
                'logo_texto': 'POS System',
                'sidebar_collapsed_default': False,
                'sidebar_theme': 'dark',
                'color_primario': '#0d6efd',
                'color_secundario': '#6c757d',
                'moneda': 'MXN',
                'simbolo_moneda': '$',
            }
        }
