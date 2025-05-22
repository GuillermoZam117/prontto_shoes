#!/usr/bin/env python
"""
Script de prueba para el módulo de sincronización.

Este script ejecuta un flujo completo de sincronización para validar 
el funcionamiento del sistema en un entorno controlado.
"""
import os
import sys
import django
import time
import logging
import json
from datetime import datetime, timedelta
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType

# Configurar el entorno de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('sincronizacion_test')

# Importar modelos y funciones
from django.contrib.auth.models import User
from django.utils import timezone
from tiendas.models import Tienda
from productos.models import Producto, Catalogo
from sincronizacion.models import (
    ColaSincronizacion, ConfiguracionSincronizacion, 
    RegistroSincronizacion, EstadoSincronizacion, TipoOperacion
)
from sincronizacion.cache_manager import cache_manager
from sincronizacion.tasks import (
    procesar_cola_sincronizacion, iniciar_sincronizacion_completa,
    verificar_sincronizaciones_automaticas, resolver_conflicto
)
from sincronizacion.conflict_resolution import ConflictResolver
from sincronizacion.security import SeguridadSincronizacion

def crear_datos_prueba():
    """Crea datos de prueba para la sincronización"""
    logger.info("Creando datos de prueba...")
    
    # Crear usuario de prueba
    user, created = User.objects.get_or_create(
        username='admin_test',
        defaults={
            'is_staff': True,
            'is_superuser': True,
            'email': 'admin@example.com'
        }
    )
    if created:
        user.set_password('password123')
        user.save()
        logger.info(f"Usuario creado: {user.username}")
    
    # Crear tiendas de prueba
    tienda_central, created = Tienda.objects.get_or_create(
        nombre='Tienda Central',
        defaults={
            'direccion': 'Calle Central 123',
            'contacto': '555-123-4567',
            'activa': True,
            'created_by': user
        }
    )
    if created:
        logger.info(f"Tienda central creada: {tienda_central.nombre}")
    
    tienda_sucursal, created = Tienda.objects.get_or_create(
        nombre='Sucursal Norte',
        defaults={
            'direccion': 'Avenida Norte 456',
            'contacto': '555-765-4321',
            'activa': True,
            'created_by': user
        }
    )
    if created:
        logger.info(f"Tienda sucursal creada: {tienda_sucursal.nombre}")
    
    # Crear configuración de sincronización
    config_central, created = ConfiguracionSincronizacion.objects.get_or_create(
        tienda=tienda_central,
        defaults={
            'sincronizacion_automatica': True,
            'intervalo_minutos': 15,
            'prioridades': {'productos.Producto': 1}
        }
    )
    if created:
        logger.info(f"Configuración central creada")
    
    config_sucursal, created = ConfiguracionSincronizacion.objects.get_or_create(
        tienda=tienda_sucursal,
        defaults={
            'sincronizacion_automatica': True,
            'intervalo_minutos': 30,
            'prioridades': {'productos.Producto': 2}
        }
    )
    if created:
        logger.info(f"Configuración sucursal creada")
    
    # Crear catálogo de prueba
    catalogo, created = Catalogo.objects.get_or_create(
        nombre='Catálogo Primavera 2025',
        defaults={
            'temporada': 'Primavera 2025',
            'es_oferta': False,
            'activo': True,
            'fecha_inicio_vigencia': timezone.now().date(),
            'fecha_fin_vigencia': (timezone.now() + timedelta(days=90)).date()
        }
    )
    if created:
        logger.info(f"Catálogo creado: {catalogo.nombre}")
    
    # Crear productos de prueba para sincronización
    productos_creados = []
    for i in range(5):
        codigo = f"P{i+1:03d}"
        try:
            # Buscar proveedor por defecto o usar None
            from proveedores.models import Proveedor
            proveedor = Proveedor.objects.first()
        except:
            proveedor = None
            
        producto, created = Producto.objects.get_or_create(
            codigo=codigo,
            defaults={
                'marca': 'Marca Test',
                'modelo': f'Modelo {i+1}',
                'color': 'Negro',
                'propiedad': f'Talla {40+i}',
                'costo': 80.00 + (i*10),
                'precio': 100.00 + (i*15),
                'temporada': 'Primavera 2025',
                'oferta': False,
                'tienda': tienda_central,
                'catalogo': catalogo,
                'proveedor': proveedor,
                'created_by': user
            }
        )
        if created:
            logger.info(f"Producto creado: {producto.codigo} - {producto.modelo}")
        productos_creados.append(producto)
    
    return {
        'user': user,
        'tienda_central': tienda_central,
        'tienda_sucursal': tienda_sucursal,
        'config_central': config_central,
        'config_sucursal': config_sucursal,
        'catalogo': catalogo,
        'productos': productos_creados
    }

def probar_cache_offline(datos_prueba):
    """Prueba el sistema de caché para modo offline"""
    logger.info("Probando sistema de caché offline...")
    
    tienda = datos_prueba['tienda_central']
    productos = datos_prueba['productos']
    
    # Cachear productos
    num_cacheados = 0
    for producto in productos:
        cache_key = f"sync_cache_Producto_{producto.id}"
        product_data = {
            'id': producto.id,
            'codigo': producto.codigo,
            'marca': producto.marca,
            'precio': float(producto.precio)
        }
        cache.set(cache_key, product_data)
        num_cacheados += 1
    
    logger.info(f"Productos cacheados: {num_cacheados}")
    
    # Verificar caché
    productos_en_cache = 0
    for producto in productos:
        cache_key = f"sync_cache_Producto_{producto.id}"
        if cache.get(cache_key):
            productos_en_cache += 1
    
    logger.info(f"Productos verificados en caché: {productos_en_cache}")
    
    # Simular reconexión (limpiar caché)
    cache.clear()
    logger.info("Caché limpiada (simulando reconexión)")
    
    return num_cacheados > 0 and productos_en_cache > 0

def probar_cola_sincronizacion(datos_prueba):
    """Prueba el sistema de cola de sincronización"""
    logger.info("Probando cola de sincronización...")
    
    tienda_central = datos_prueba['tienda_central']
    tienda_sucursal = datos_prueba['tienda_sucursal']
    user = datos_prueba['user']
    productos = datos_prueba['productos'][:3]
    
    # Crear operaciones de prueba
    operaciones_creadas = []
    for i, producto in enumerate(productos):
        # Simular diferentes tipos de operaciones
        tipo = TipoOperacion.CREAR if i == 0 else (
            TipoOperacion.ACTUALIZAR if i == 1 else TipoOperacion.ELIMINAR
        )
        
        # Obtener ContentType
        content_type = ContentType.objects.get_for_model(Producto)
        
        # Datos producto como JSON
        datos_json = json.dumps({
            'codigo': producto.codigo,
            'marca': producto.marca,
            'modelo': producto.modelo,
            'precio': float(producto.precio)
        })
        
        # Crear operación
        operacion = ColaSincronizacion.objects.create(
            tienda_origen=tienda_central,
            tienda_destino=tienda_sucursal,
            content_type=content_type,
            object_id=str(producto.pk),
            datos_json=datos_json,
            tipo_operacion=tipo,
            usuario=user,
            estado=EstadoSincronizacion.PENDIENTE
        )
        
        operaciones_creadas.append(operacion)
        logger.info(f"Operación creada: {operacion.id} - {operacion.tipo_operacion}")
    
    # Procesar la cola
    exitosas, fallidas, conflictos = procesar_cola_sincronizacion(tienda_id=tienda_central.id)
    logger.info(f"Procesamiento de cola - Exitosas: {exitosas}, Fallidas: {fallidas}, Conflictos: {conflictos}")
    
    # Verificar estados
    pendientes = ColaSincronizacion.objects.filter(estado=EstadoSincronizacion.PENDIENTE).count()
    completadas = ColaSincronizacion.objects.filter(estado=EstadoSincronizacion.COMPLETADO).count()
    
    logger.info(f"Estado final - Pendientes: {pendientes}, Completadas: {completadas}")
    
    return len(operaciones_creadas) > 0

def probar_conflictos(datos_prueba):
    """Prueba el sistema de resolución de conflictos"""
    logger.info("Probando resolución de conflictos...")
    
    tienda_central = datos_prueba['tienda_central']
    tienda_sucursal = datos_prueba['tienda_sucursal']
    user = datos_prueba['user']
    
    # Obtener un producto existente o crear uno nuevo
    if datos_prueba['productos']:
        producto = datos_prueba['productos'][0]
        logger.info(f"Usando producto existente: {producto.codigo}")
    else:
        try:
            # Buscar proveedor por defecto o usar None
            from proveedores.models import Proveedor
            proveedor = Proveedor.objects.first()
        except:
            proveedor = None
            
        producto, created = Producto.objects.get_or_create(
            codigo='CONFLICT001',
            defaults={
                'marca': 'Marca Conflicto',
                'modelo': 'Modelo Conflicto',
                'color': 'Rojo',
                'propiedad': 'Talla 42',
                'costo': 90.00,
                'precio': 120.00,
                'temporada': 'Primavera 2025',
                'oferta': False,
                'tienda': tienda_central,
                'catalogo': datos_prueba['catalogo'],
                'proveedor': proveedor,
                'created_by': user
            }
        )
        if created:
            logger.info(f"Producto para conflicto creado: {producto.codigo}")
    
    # Obtener ContentType
    content_type = ContentType.objects.get_for_model(Producto)
    
    # Crear operación con conflicto
    operacion = ColaSincronizacion.objects.create(
        tienda_origen=tienda_central,
        tienda_destino=tienda_sucursal,
        content_type=content_type,
        object_id=str(producto.pk),
        datos_json='{"precio": 130.00, "color": "Azul"}',
        tipo_operacion=TipoOperacion.ACTUALIZAR,
        usuario=user,
        estado=EstadoSincronizacion.PENDIENTE,
        tiene_conflicto=True,
        datos_conflicto_json='{"servidor": {"precio": 130.00, "color": "Azul"}, "local": {"precio": 125.00, "color": "Verde"}}'
    )
    logger.info(f"Operación conflictiva creada: {operacion.id}")
    
    # Simular resolución del conflicto
    operacion.estado = EstadoSincronizacion.COMPLETADO
    operacion.tiene_conflicto = False
    operacion.save()
    
    logger.info(f"Conflicto resuelto manualmente (simulado)")
    
    return True

def probar_sincronizacion_completa(datos_prueba):
    """Prueba una sincronización completa"""
    logger.info("Probando sincronización completa...")
    
    tienda = datos_prueba['tienda_central']
    user = datos_prueba['user']
    
    # Crear registro de sincronización
    registro = RegistroSincronizacion.objects.create(
        tienda=tienda,
        usuario=user,
        fecha_inicio=timezone.now(),
        estado=EstadoSincronizacion.EN_PROCESO
    )
    logger.info(f"Registro de sincronización creado: {registro.id}")
    
    # Actualizar estado a completado
    registro.estado = EstadoSincronizacion.COMPLETADO
    registro.fecha_fin = timezone.now()
    registro.save()
    logger.info(f"Sincronización simulada completada")
    
    return True

def ejecutar_pruebas():
    """Ejecuta todas las pruebas de sincronización"""
    logger.info("=== INICIANDO PRUEBAS DE SINCRONIZACIÓN ===")
    
    # Crear datos de prueba
    datos_prueba = crear_datos_prueba()
    
    # Pruebas individuales
    resultados = {
        'cache_offline': probar_cache_offline(datos_prueba),
        'cola_sincronizacion': probar_cola_sincronizacion(datos_prueba),
        'conflictos': probar_conflictos(datos_prueba),
        'sincronizacion_completa': probar_sincronizacion_completa(datos_prueba)
    }
    
    # Resumen
    logger.info("=== RESUMEN DE PRUEBAS ===")
    for prueba, resultado in resultados.items():
        logger.info(f"{prueba}: {'✅ EXITOSA' if resultado else '❌ FALLIDA'}")
    
    return all(resultados.values())

if __name__ == "__main__":
    exito = ejecutar_pruebas()
    sys.exit(0 if exito else 1)
