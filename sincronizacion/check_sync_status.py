#!/usr/bin/env python
"""
Script para verificar el estado del sistema de sincronización.
Ejecutar desde la línea de comandos para obtener un resumen rápido.
"""
import os
import sys
import django
import json
import argparse
from datetime import datetime, timedelta

# Configurar entorno Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from django.utils import timezone
from django.db.models import Count, Q
from django.core.cache import cache
from tiendas.models import Tienda
from sincronizacion.models import (
    ColaSincronizacion, ConfiguracionSincronizacion, 
    RegistroSincronizacion, EstadoSincronizacion, TipoOperacion
)
from sincronizacion.cache_manager import detectar_estado_conexion, CACHE_DIR, CACHE_PREFIX
from django.contrib.contenttypes.models import ContentType
from sincronizacion.websocket import notificar_cambio_estado, notificar_conflicto
from sincronizacion.performance_optimizations import (
    refrescar_cache_incremental, ajustar_prioridades_dinamicas
)

def formatear_tiempo(segundos):
    """Formatea un tiempo en segundos a un formato legible"""
    if segundos < 60:
        return f"{int(segundos)} segundos"
    elif segundos < 3600:
        return f"{int(segundos/60)} minutos"
    elif segundos < 86400:
        return f"{int(segundos/3600)} horas"
    else:
        return f"{int(segundos/86400)} días"

def verificar_sincronizacion():
    """Verifica y muestra el estado del sistema de sincronización"""
    # Estado de conexión
    try:
        online = detectar_estado_conexion()
        print(f"\n🌐 Estado de conexión: {'✅ ONLINE' if online else '❌ OFFLINE'}")
    except:
        print("\n🌐 Estado de conexión: ❓ NO DETECTABLE")
    
    # Tiendas activas
    tiendas = Tienda.objects.filter(activa=True).count()
    print(f"\n🏪 Tiendas activas: {tiendas}")
    
    # Operaciones pendientes
    pendientes = ColaSincronizacion.objects.filter(estado=EstadoSincronizacion.PENDIENTE).count()
    print(f"\n⏳ Operaciones pendientes: {pendientes}")
    
    # Desglose por tipo de operación
    tipos = ColaSincronizacion.objects.filter(
        estado=EstadoSincronizacion.PENDIENTE
    ).values('tipo_operacion').annotate(total=Count('id'))
    
    if tipos:
        print("\n📊 Desglose por tipo:")
        for tipo in tipos:
            print(f"  - {tipo['tipo_operacion']}: {tipo['total']}")
    
    # Conflictos
    conflictos = ColaSincronizacion.objects.filter(tiene_conflicto=True).count()
    print(f"\n⚠️ Conflictos: {conflictos}")
    
    if conflictos > 0:
        print("\n📋 Detalle de conflictos:")
        for conflicto in ColaSincronizacion.objects.filter(tiene_conflicto=True):
            content_type = ContentType.objects.get(id=conflicto.content_type_id)
            print(f"  - {content_type.app_label}.{content_type.model} (ID: {conflicto.object_id})")
    
    # Última sincronización
    try:
        ultima = RegistroSincronizacion.objects.filter(
            estado=EstadoSincronizacion.COMPLETADO
        ).order_by('-fecha_fin').first()
        
        if ultima:
            tiempo_desde = (timezone.now() - ultima.fecha_fin).total_seconds()
            print(f"\n🕒 Última sincronización: hace {formatear_tiempo(tiempo_desde)}")
        else:
            print("\n🕒 Última sincronización: nunca")
    except:
        print("\n🕒 Última sincronización: error al obtener")
    
    # Verificar caché
    try:
        keys = cache.keys('sync_cache_*')
        print(f"\n💾 Objetos en caché: {len(keys) if keys else 0}")
    except:
        print("\n💾 Objetos en caché: error al obtener")
    
    # Comprobar si hay alguna sincronización en curso
    en_proceso = RegistroSincronizacion.objects.filter(
        estado=EstadoSincronizacion.EN_PROCESO
    ).count()
    
    if en_proceso:
        print(f"\n🔄 Sincronizaciones en curso: {en_proceso}")
    
    # Estado general
    if pendientes > 100 or conflictos > 0:
        print("\n🚨 ESTADO GENERAL: REQUIERE ATENCIÓN")
    elif not online:
        print("\n⚠️ ESTADO GENERAL: MODO OFFLINE")
    else:
        print("\n✅ ESTADO GENERAL: NORMAL")
    
    print("\n")

def verificar_optimizaciones_rendimiento():
    """Verifica y prueba las optimizaciones de rendimiento"""
    print("\n=============================================")
    print("   PRUEBAS DE OPTIMIZACIONES DE RENDIMIENTO")
    print("=============================================")
    
    # Probar refresco incremental de caché
    try:
        print("\n📊 Probando refresco incremental de caché...")
        start_time = timezone.now()
        actualizados = refrescar_cache_incremental()
        tiempo = (timezone.now() - start_time).total_seconds()
        print(f"✅ Refresco incremental completado: {actualizados} registros en {tiempo:.2f} segundos")
    except Exception as e:
        print(f"❌ Error al probar refresco incremental: {e}")
    
    # Probar ajuste dinámico de prioridades
    try:
        print("\n📊 Probando ajuste dinámico de prioridades...")
        start_time = timezone.now()
        resultado = ajustar_prioridades_dinamicas()
        tiempo = (timezone.now() - start_time).total_seconds()
        estado = "✅ Completado" if resultado else "❌ No completado"
        print(f"{estado} en {tiempo:.2f} segundos")
    except Exception as e:
        print(f"❌ Error al probar ajuste de prioridades: {e}")
    
    # Probar notificaciones WebSocket
    try:
        print("\n📊 Probando notificaciones WebSocket...")
        start_time = timezone.now()
        resultado = notificar_cambio_estado()
        tiempo = (timezone.now() - start_time).total_seconds()
        estado = "✅ Enviado" if resultado else "❌ Error"
        print(f"Estado: {estado} en {tiempo:.2f} segundos")
    except Exception as e:
        print(f"❌ Error al probar notificaciones: {e}")
    
    print("\n=============================================")


if __name__ == "__main__":
    print("\n=============================================")
    print("   ESTADO DEL SISTEMA DE SINCRONIZACIÓN")
    print("=============================================")
    
    verificar_sincronizacion()
    
    # Verificar optimizaciones si se pasa el argumento --optimizaciones
    if len(sys.argv) > 1 and sys.argv[1] == '--optimizaciones':
        verificar_optimizaciones_rendimiento()
