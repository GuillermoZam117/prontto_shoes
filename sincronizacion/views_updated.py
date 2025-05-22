from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.apps import apps
from django.contrib import messages
from django.http import JsonResponse
from django.utils.timezone import now, timedelta
from tiendas.models import Tienda

from .models import ColaSincronizacion, ConfiguracionSincronizacion, RegistroSincronizacion, EstadoSincronizacion
from .serializers import (
    ColaSincronizacionSerializer, ConfiguracionSincronizacionSerializer,
    RegistroSincronizacionSerializer, ContentTypeSerializer, RegistroAuditoriaSerializer
)
from .tasks import (
    procesar_cola_sincronizacion, iniciar_sincronizacion_completa,
    verificar_sincronizaciones_automaticas, resolver_conflicto as resolver_conflicto_task
)
from .security import RegistroAuditoria, SeguridadSincronizacion
from .conflict_resolution import ConflictResolver, ConflictResolutionStrategy
from .performance_optimizations import (
    refrescar_cache_incremental, cache_model_batch,
    detectar_conflictos_potenciales, ajustar_prioridades_dinamicas,
    procesar_cola_rapido
)

# Updated resolver_conflicto function with proper task reference
@login_required
def resolver_conflicto(request, operacion_id):
    """
    Vista para resolver conflictos de sincronización
    """
    operacion = get_object_or_404(ColaSincronizacion, id=operacion_id)
    
    # Verificar si realmente hay un conflicto
    if not operacion.tiene_conflicto:
        messages.error(request, 'La operación no tiene conflictos para resolver.')
        return redirect('sincronizacion:cola_sincronizacion')
    
    if request.method == 'POST':
        # Obtener decisión del usuario
        decision = request.POST.get('decision', '')
        
        if decision == 'servidor':
            # Usar datos del servidor
            resultado = resolver_conflicto_task(
                operacion_id=operacion.id,
                usar_datos_servidor=True,
                usuario=request.user
            )
        elif decision == 'local':
            # Usar datos locales
            resultado = resolver_conflicto_task(
                operacion_id=operacion.id,
                usar_datos_servidor=False,
                usuario=request.user
            )
        elif decision == 'personalizado':
            # Datos personalizados (simplificado)
            datos_personalizados = request.POST.get('datos_personalizados', '{}')
            import json
            try:
                datos_json = json.loads(datos_personalizados)
                resultado = resolver_conflicto_task(
                    operacion_id=operacion.id,
                    usar_datos_servidor=False,
                    datos_personalizados=datos_json,
                    usuario=request.user
                )
            except json.JSONDecodeError:
                messages.error(request, 'Error en el formato de los datos personalizados.')
                return redirect('sincronizacion:resolver_conflicto', operacion_id=operacion_id)
        else:
            messages.error(request, 'Opción de resolución no válida.')
            return redirect('sincronizacion:resolver_conflicto', operacion_id=operacion_id)
        
        if resultado:
            messages.success(request, 'Conflicto resuelto correctamente.')
            return redirect('sincronizacion:cola_sincronizacion')
        else:
            messages.error(request, 'Error al resolver el conflicto.')
    
    # Obtener modelo y datos
    content_type = operacion.content_type
    model_class = content_type.model_class()
    model_name = f"{content_type.app_label}.{content_type.model}"
    
    # Preparar contexto para la plantilla
    context = {
        'operacion': operacion,
        'model_name': model_name,
        'datos_locales': operacion.datos,
        'datos_servidor': operacion.datos_servidor or {},
        'diferencias': operacion.diferencias or []
    }
    
    return render(request, 'sincronizacion/resolver_conflicto.html', context)
