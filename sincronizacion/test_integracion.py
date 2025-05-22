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
from datetime import datetime, timedelta

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
    for i in range(5):
        codigo = f"P{i+1:03d}"
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
                'proveedor': None,  # Establecer si es necesario
                'created_by': user
            }
        )
        if created:
            logger.info(f"Producto creado: {producto.codigo} - {producto.modelo}")
    
    return {
        'user': user,
        'tienda_central': tienda_central,
        'tienda_sucursal': tienda_sucursal,
        'config_central': config_central,
        'config_sucursal': config_sucursal,
        'catalogo': catalogo
    }

def probar_cache_offline(datos_prueba):
    """Prueba el sistema de caché para modo offline"""
    logger.info("Probando sistema de caché offline...")
    
    tienda = datos_prueba['tienda_central']
    
    # Cachear productos críticos
    productos = Producto.objects.filter(tienda=tienda)
    num_cacheados = 0
    for producto in productos:
        if cache_manager.cache_instance(Producto, producto.pk):
            num_cacheados += 1
    logger.info(f"Productos cacheados: {num_cacheados}")
    
    # Verificar cacheado
    cached_products = cache_manager.get_cached_queryset(Producto)
    logger.info(f"Productos en caché: {len(cached_products)}")
    
    # Forzar guardado en disco
    for producto in productos:
        cache_key = cache_manager.get_cache_key(Producto, producto.pk)
        cache_manager.persist_to_disk(cache_key, cache_manager.get_cached_instance(Producto, producto.pk))
    
    logger.info(f"Productos guardados en disco")
    
    # Simular reconexión (limpiar caché en memoria)
    from django.core.cache import cache
    cache.clear()
    logger.info(f"Caché en memoria limpiada (simulando reconexión)")
    
    # Verificar carga desde disco
    cached_after_clear = cache_manager.get_cached_queryset(Producto)
    logger.info(f"Productos recuperados del disco: {len(cached_after_clear)}")
    
    return len(cached_after_clear) > 0

def probar_cola_sincronizacion(datos_prueba):
    """Prueba el sistema de cola de sincronización"""
    logger.info("Probando cola de sincronización...")
    
    tienda_central = datos_prueba['tienda_central']
    tienda_sucursal = datos_prueba['tienda_sucursal']
    user = datos_prueba['user']
    
    # Crear operaciones de prueba
    productos = Producto.objects.filter(tienda=tienda_central)[:3]
    
    operaciones_creadas = []
    for i, producto in enumerate(productos):
        # Simular diferentes tipos de operaciones
        tipo = TipoOperacion.CREAR if i == 0 else (
            TipoOperacion.ACTUALIZAR if i == 1 else TipoOperacion.ELIMINAR
        )
        
        # Obtener ContentType
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(Producto)
        
        # Datos producto como JSON
        import json
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
    
    return completadas > 0

def probar_conflictos(datos_prueba):
    """Prueba el sistema de resolución de conflictos"""
    logger.info("Probando resolución de conflictos...")
    
    tienda_central = datos_prueba['tienda_central']
    tienda_sucursal = datos_prueba['tienda_sucursal']
    user = datos_prueba['user']
    
    # Crear un producto que será modificado en ambas tiendas
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
            'proveedor': None,
            'created_by': user
        }
    )
    if created:
        logger.info(f"Producto para conflicto creado: {producto.codigo}")
    
    # Crear operaciones conflictivas
    operacion1 = ColaSincronizacion.objects.create(
        tienda_origen=tienda_central,
        tienda_destino=tienda_sucursal,
        content_type=producto.get_content_type(),
        object_id=str(producto.pk),
        datos_json='{"precio": 130.00, "color": "Azul"}',
        tipo_operacion=TipoOperacion.ACTUALIZAR,
        usuario=user,
        estado=EstadoSincronizacion.PENDIENTE,
        tiene_conflicto=True,
        datos_conflicto_json='{"servidor": {"precio": 130.00, "color": "Azul"}, "local": {"precio": 125.00, "color": "Verde"}}'
    )
    logger.info(f"Operación conflictiva creada: {operacion1.id}")
    
    # Resolver conflicto
    resolver_conflicto(
        operacion1.id,
        usar_datos_servidor=True,
        datos_personalizados=None,
        usuario=user
    )
    
    # Verificar estado
    operacion1.refresh_from_db()
    logger.info(f"Estado después de resolución: {operacion1.estado}")
    
    return operacion1.estado == EstadoSincronizacion.COMPLETADO and not operacion1.tiene_conflicto

def probar_sincronizacion_completa(datos_prueba):
    """Prueba una sincronización completa"""
    logger.info("Probando sincronización completa...")
    
    tienda = datos_prueba['tienda_central']
    user = datos_prueba['user']
    
    # Iniciar sincronización completa
    registro_id = iniciar_sincronizacion_completa(tienda.id, usuario=user)
    logger.info(f"Sincronización iniciada: {registro_id}")
    
    # Esperar a que se complete
    time.sleep(2)
    
    # Verificar estado
    if registro_id:
        registro = RegistroSincronizacion.objects.get(id=registro_id)
        logger.info(f"Estado de sincronización: {registro.estado}")
        
        return registro.estado == EstadoSincronizacion.COMPLETADO
    
    return False

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
