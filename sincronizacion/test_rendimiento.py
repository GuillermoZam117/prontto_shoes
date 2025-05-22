#!/usr/bin/env python
"""
Script de prueba mejorado para el módulo de sincronización.

Este script ejecuta un flujo completo de sincronización para validar 
el rendimiento del sistema con volúmenes de datos más grandes.
"""
import os
import sys
import django
import time
import logging
import json
import random
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

logger = logging.getLogger('sincronizacion_test_volumen')

# Importar modelos y funciones
from django.contrib.auth.models import User
from django.utils import timezone
from tiendas.models import Tienda
from productos.models import Producto, Categoria
from clientes.models import Cliente
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
from sincronizacion.performance_optimizations import (
    refrescar_cache_incremental, cache_model_batch,
    procesar_cola_rapido, ajustar_prioridades_dinamicas
)

def crear_datos_prueba_volumen(n_productos=100, n_clientes=50):
    """Crea un volumen mayor de datos de prueba para pruebas de rendimiento"""
    logger.info(f"Creando datos de prueba de volumen... ({n_productos} productos, {n_clientes} clientes)")
    
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
            'prioridades': {'productos.Producto': 1, 'clientes.Cliente': 2}
        }
    )
    
    config_sucursal, created = ConfiguracionSincronizacion.objects.get_or_create(
        tienda=tienda_sucursal,
        defaults={
            'sincronizacion_automatica': True,
            'intervalo_minutos': 30,
            'prioridades': {'productos.Producto': 1, 'clientes.Cliente': 2}
        }
    )
    
    # Crear categorías
    categorias = [
        Categoria.objects.get_or_create(
            nombre=f'Categoría {i}',
            defaults={'descripcion': f'Descripción de categoría {i}'}
        )[0] for i in range(1, 6)
    ]
    
    # Crear productos en volumen
    productos_creados = 0
    for i in range(1, n_productos + 1):
        # Alternar tienda para los productos
        tienda = tienda_central if i % 2 == 0 else tienda_sucursal
        categoria = random.choice(categorias)
        
        try:
            producto, created = Producto.objects.get_or_create(
                codigo=f'PROD{i:04d}',
                defaults={
                    'nombre': f'Producto de prueba {i}',
                    'descripcion': f'Descripción del producto {i}',
                    'precio': round(random.uniform(10.0, 999.99), 2),
                    'stock': random.randint(1, 100),
                    'categoria': categoria,
                    'tienda': tienda
                }
            )
            if created:
                productos_creados += 1
        except Exception as e:
            logger.error(f"Error al crear producto {i}: {e}")
    
    logger.info(f"Productos creados: {productos_creados}")
    
    # Crear clientes en volumen
    clientes_creados = 0
    for i in range(1, n_clientes + 1):
        # Alternar tienda para los clientes
        tienda = tienda_central if i % 2 == 0 else tienda_sucursal
        
        try:
            cliente, created = Cliente.objects.get_or_create(
                dni=f'C{i:08d}',
                defaults={
                    'nombre': f'Cliente {i}',
                    'apellidos': f'Apellido {i}',
                    'email': f'cliente{i}@example.com',
                    'telefono': f'555-{i:03d}-{i+100:04d}',
                    'tienda': tienda
                }
            )
            if created:
                clientes_creados += 1
        except Exception as e:
            logger.error(f"Error al crear cliente {i}: {e}")
    
    logger.info(f"Clientes creados: {clientes_creados}")
    
    return tienda_central, tienda_sucursal

def generar_cola_sincronizacion(n_operaciones=100):
    """Genera un conjunto de operaciones de sincronización para pruebas"""
    logger.info(f"Generando cola de sincronización con {n_operaciones} operaciones...")
    
    # Obtener todas las tiendas
    tiendas = list(Tienda.objects.filter(activa=True))
    if not tiendas:
        logger.error("No hay tiendas activas")
        return 0
    
    # Obtener todos los productos
    productos = list(Producto.objects.all())
    if not productos:
        logger.error("No hay productos disponibles")
        return 0
    
    # Obtener todos los clientes
    clientes = list(Cliente.objects.all())
    if not clientes:
        logger.error("No hay clientes disponibles")
        return 0
    
    # Content types
    producto_ct = ContentType.objects.get_for_model(Producto)
    cliente_ct = ContentType.objects.get_for_model(Cliente)
    
    # Tipos de operaciones
    tipos_operacion = [TipoOperacion.CREAR, TipoOperacion.ACTUALIZAR, TipoOperacion.ELIMINAR]
    
    operaciones_creadas = 0
    
    # Generar operaciones aleatorias
    for i in range(n_operaciones):
        try:
            # Elegir tipo de modelo aleatorio (70% productos, 30% clientes)
            if random.random() < 0.7:
                content_type = producto_ct
                objeto = random.choice(productos)
                datos = {
                    'id': objeto.id,
                    'nombre': objeto.nombre,
                    'codigo': objeto.codigo,
                    'precio': float(objeto.precio),
                    'stock': random.randint(1, 100)  # Stock aleatorio para generar conflictos
                }
            else:
                content_type = cliente_ct
                objeto = random.choice(clientes)
                datos = {
                    'id': objeto.id,
                    'nombre': objeto.nombre,
                    'apellidos': objeto.apellidos,
                    'dni': objeto.dni,
                    'email': objeto.email
                }
            
            # Elegir tipo de operación (60% actualizar, 30% crear, 10% eliminar)
            rand = random.random()
            if rand < 0.6:
                tipo_operacion = TipoOperacion.ACTUALIZAR
            elif rand < 0.9:
                tipo_operacion = TipoOperacion.CREAR
            else:
                tipo_operacion = TipoOperacion.ELIMINAR
            
            # Elegir tiendas origen y destino
            tienda_origen = random.choice(tiendas)
            tienda_destino = random.choice([t for t in tiendas if t != tienda_origen]) if len(tiendas) > 1 else tienda_origen
            
            # Prioridad (1-10)
            prioridad = random.randint(1, 10)
            
            # Crear operación
            operacion = ColaSincronizacion.objects.create(
                tienda_origen=tienda_origen,
                tienda_destino=tienda_destino,
                content_type=content_type,
                object_id=objeto.id,
                tipo_operacion=tipo_operacion,
                estado=EstadoSincronizacion.PENDIENTE,
                datos=datos,
                prioridad=prioridad
            )
            
            operaciones_creadas += 1
            
        except Exception as e:
            logger.error(f"Error al crear operación {i}: {e}")
    
    logger.info(f"Operaciones creadas en cola: {operaciones_creadas}")
    return operaciones_creadas

def probar_cache_rendimiento():
    """Prueba el rendimiento del sistema de caché"""
    logger.info("Probando rendimiento del sistema de caché...")
    
    # Limpiar caché para pruebas
    cache.clear()
    
    # Medir tiempo para refresco completo
    inicio = time.time()
    productos = Producto.objects.all()
    n_productos = productos.count()
    
    for producto in productos:
        cache_manager.cache_model_instance(producto)
    
    tiempo_individual = time.time() - inicio
    logger.info(f"Tiempo para cachear {n_productos} productos individualmente: {tiempo_individual:.2f} segundos")
    
    # Limpiar caché para pruebas
    cache.clear()
    
    # Medir tiempo para refresco por lotes
    inicio = time.time()
    batch_size = 50
    total = cache_model_batch(Producto, batch_size=batch_size)
    tiempo_lotes = time.time() - inicio
    
    logger.info(f"Tiempo para cachear {total} productos por lotes (batch_size={batch_size}): {tiempo_lotes:.2f} segundos")
    logger.info(f"Mejora de rendimiento: {(tiempo_individual / tiempo_lotes):.2f}x")
    
    # Probar refresco incremental
    inicio = time.time()
    # Modificar algunos productos para simular cambios recientes
    productos_muestra = Producto.objects.all()[:20]
    for p in productos_muestra:
        p.precio = float(p.precio) * 1.05  # Aumento de 5%
        p.save()
    
    # Ejecutar refresco incremental
    actualizados = refrescar_cache_incremental()
    tiempo_incremental = time.time() - inicio
    
    logger.info(f"Tiempo para refresco incremental de {actualizados} productos: {tiempo_incremental:.2f} segundos")
    
    return {
        'tiempo_individual': tiempo_individual,
        'tiempo_lotes': tiempo_lotes,
        'tiempo_incremental': tiempo_incremental,
        'mejora_factor': tiempo_individual / tiempo_lotes
    }

def probar_cola_rendimiento(n_operaciones=100):
    """Prueba el rendimiento del procesamiento de cola"""
    logger.info(f"Probando rendimiento del procesamiento de cola con {n_operaciones} operaciones...")
    
    # Generar operaciones de prueba
    generar_cola_sincronizacion(n_operaciones)
    
    # Medir tiempo para procesamiento estándar
    inicio = time.time()
    resultado_estandar = procesar_cola_sincronizacion()
    tiempo_estandar = time.time() - inicio
    
    logger.info(f"Tiempo procesamiento estándar: {tiempo_estandar:.2f} segundos")
    
    # Generar más operaciones de prueba
    generar_cola_sincronizacion(n_operaciones)
    
    # Medir tiempo para procesamiento optimizado
    inicio = time.time()
    resultado_optimizado = procesar_cola_rapido()
    tiempo_optimizado = time.time() - inicio
    
    logger.info(f"Tiempo procesamiento optimizado: {tiempo_optimizado:.2f} segundos")
    logger.info(f"Mejora de rendimiento: {(tiempo_estandar / tiempo_optimizado):.2f}x")
    
    return {
        'tiempo_estandar': tiempo_estandar,
        'tiempo_optimizado': tiempo_optimizado,
        'mejora_factor': tiempo_estandar / tiempo_optimizado
    }

def main():
    """Función principal de prueba"""
    logger.info("=== INICIANDO PRUEBAS DE RENDIMIENTO DEL SISTEMA DE SINCRONIZACIÓN ===")
    
    try:
        # 1. Crear datos de prueba en volumen
        tienda_central, tienda_sucursal = crear_datos_prueba_volumen(
            n_productos=200,  # 200 productos
            n_clientes=100    # 100 clientes
        )
        
        # 2. Probar rendimiento del sistema de caché
        resultados_cache = probar_cache_rendimiento()
        
        # 3. Probar rendimiento del procesamiento de cola
        resultados_cola = probar_cola_rendimiento(n_operaciones=100)
        
        # 4. Probar ajuste dinámico de prioridades
        logger.info("Probando ajuste dinámico de prioridades...")
        ajustar_prioridades_dinamicas()
        
        # 5. Resumen de resultados
        logger.info("\n=== RESUMEN DE RESULTADOS ===")
        logger.info(f"Mejora en rendimiento de caché: {resultados_cache['mejora_factor']:.2f}x")
        logger.info(f"Mejora en procesamiento de cola: {resultados_cola['mejora_factor']:.2f}x")
        
        logger.info("\n=== PRUEBAS DE RENDIMIENTO COMPLETADAS CON ÉXITO ===")
        return 0
        
    except Exception as e:
        logger.error(f"Error en pruebas de rendimiento: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
