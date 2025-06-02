"""
Views for business configuration management
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .models import ConfiguracionNegocio
from .serializers import ConfiguracionNegocioSerializer


@login_required
def configuracion_management(request):
    """
    View for managing business configuration through web interface
    """
    config = ConfiguracionNegocio.get_configuracion()
    
    if request.method == 'POST':
        try:
            # Handle form submission
            config.nombre_negocio = request.POST.get('nombre_negocio', config.nombre_negocio)
            config.eslogan = request.POST.get('eslogan', config.eslogan)
            config.logo_texto = request.POST.get('logo_texto', config.logo_texto)
            config.color_primario = request.POST.get('color_primario', config.color_primario)
            config.color_secundario = request.POST.get('color_secundario', config.color_secundario)
            config.sidebar_theme = request.POST.get('sidebar_theme', config.sidebar_theme)
            config.sidebar_collapsed_default = 'sidebar_collapsed_default' in request.POST
            config.moneda = request.POST.get('moneda', config.moneda)
            config.simbolo_moneda = request.POST.get('simbolo_moneda', config.simbolo_moneda)
            config.idioma = request.POST.get('idioma', config.idioma)
              # Handle logo upload
            if 'logo' in request.FILES:
                config.logo = request.FILES['logo']
            config.updated_by = request.user
            config.save()
            
            messages.success(request, 'Configuración actualizada exitosamente.')
            return redirect('configuracion:gestion_configuracion')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar la configuración: {str(e)}')
    
    context = {
        'config': config,
        'page_title': 'Configuración del Negocio',
    }
    
    return render(request, 'configuracion/management.html', context)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def reset_sidebar_settings(request):
    """
    Reset sidebar settings to default
    """
    try:
        data = json.loads(request.body)
        config = ConfiguracionNegocio.get_configuracion()
        
        config.sidebar_collapsed_default = data.get('collapsed', False)
        config.sidebar_theme = data.get('theme', 'dark')
        config.updated_by = request.user
        config.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Configuración del sidebar actualizada'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def test_sidebar_config(request):
    """
    Test view to demonstrate sidebar configuration changes
    """
    config = ConfiguracionNegocio.get_configuracion()
    
    context = {
        'config': config,
        'page_title': 'Test Sidebar Configuration',
    }
    
    return render(request, 'configuracion/test_sidebar.html', context)
