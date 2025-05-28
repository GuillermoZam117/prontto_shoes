from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.conf import settings
import os

from .models import ConfiguracionNegocio, InformacionContacto, DetallesImpresion
from .serializers import (
    ConfiguracionNegocioSerializer,
    InformacionContactoSerializer,
    DetallesImpresionSerializer,
    LogotipoSerializer,
    ConfiguracionCompletaSerializer
)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def configuracion_negocio(request):
    """
    Endpoint para obtener y actualizar la configuración del negocio
    GET: Obtiene la configuración actual
    PUT: Actualiza la configuración
    """
    config = ConfiguracionNegocio.get_configuracion()
    
    if request.method == 'GET':
        serializer = ConfiguracionNegocioSerializer(config, context={'request': request})
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        # Actualizar usuario que modifica
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.data['updated_by'] = request.user.id
        
        serializer = ConfiguracionNegocioSerializer(
            config, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(updated_by=request.user if request.user.is_authenticated else None)
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def logotipo(request):
    """
    Endpoint para manejo del logotipo
    GET: Obtiene información del logo actual
    POST: Sube un nuevo logo
    DELETE: Elimina el logo actual
    """
    config = ConfiguracionNegocio.get_configuracion()
    
    if request.method == 'GET':
        data = {
            'logo_url': None,
            'logo_texto': config.logo_texto,
            'has_logo': bool(config.logo)
        }
        
        if config.logo:
            data['logo_url'] = request.build_absolute_uri(config.logo.url)
        
        return Response(data)
    
    elif request.method == 'POST':
        serializer = LogotipoSerializer(data=request.data)
        
        if serializer.is_valid():
            # Eliminar logo anterior si existe
            if config.logo:
                if default_storage.exists(config.logo.name):
                    default_storage.delete(config.logo.name)
            
            # Guardar nuevo logo
            config.logo = serializer.validated_data['logo']
            if 'logo_texto' in serializer.validated_data:
                config.logo_texto = serializer.validated_data['logo_texto']
            
            config.updated_by = request.user if request.user.is_authenticated else None
            config.save()
            
            response_data = {
                'message': 'Logo actualizado exitosamente',
                'logo_url': request.build_absolute_uri(config.logo.url),
                'logo_texto': config.logo_texto
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        if config.logo:
            # Eliminar archivo físico
            if default_storage.exists(config.logo.name):
                default_storage.delete(config.logo.name)
            
            # Limpiar campo en la base de datos
            config.logo = None
            config.updated_by = request.user if request.user.is_authenticated else None
            config.save()
            
            return Response({'message': 'Logo eliminado exitosamente'})
        
        return Response(
            {'message': 'No hay logo para eliminar'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def informacion_contacto(request):
    """
    Endpoint para información de contacto
    GET: Obtiene la información de contacto
    PUT: Actualiza la información de contacto
    """
    config = ConfiguracionNegocio.get_configuracion()
    contacto, created = InformacionContacto.objects.get_or_create(
        configuracion=config
    )
    
    if request.method == 'GET':
        serializer = InformacionContactoSerializer(contacto)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = InformacionContactoSerializer(
            contacto, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def detalles_impresion(request):
    """
    Endpoint para detalles de impresión
    GET: Obtiene los detalles de impresión
    PUT: Actualiza los detalles de impresión
    """
    config = ConfiguracionNegocio.get_configuracion()
    impresion, created = DetallesImpresion.objects.get_or_create(
        configuracion=config
    )
    
    if request.method == 'GET':
        serializer = DetallesImpresionSerializer(impresion)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = DetallesImpresionSerializer(
            impresion, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def configuracion_completa(request):
    """
    Endpoint para obtener toda la configuración del negocio
    GET: Obtiene configuración completa (negocio + contacto + impresión)
    """
    config = ConfiguracionNegocio.get_configuracion()
    
    # Asegurar que existan los registros relacionados
    InformacionContacto.objects.get_or_create(configuracion=config)
    DetallesImpresion.objects.get_or_create(configuracion=config)
    
    serializer = ConfiguracionCompletaSerializer(config, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def configuracion_publica(request):
    """
    Endpoint público para obtener configuración básica del negocio
    (sin autenticación requerida)
    """
    config = ConfiguracionNegocio.get_configuracion()
    
    data = {
        'nombre_negocio': config.nombre_negocio,
        'eslogan': config.eslogan,
        'logo_url': None,
        'logo_texto': config.logo_texto,
        'color_primario': config.color_primario,
        'color_secundario': config.color_secundario,
        'sidebar_theme': config.sidebar_theme,
        'sidebar_collapsed_default': config.sidebar_collapsed_default,
        'moneda': config.moneda,
        'simbolo_moneda': config.simbolo_moneda,
        'idioma': config.idioma
    }
    
    if config.logo:
        data['logo_url'] = request.build_absolute_uri(config.logo.url)
    
    return Response(data)
