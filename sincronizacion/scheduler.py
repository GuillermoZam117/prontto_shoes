import time
import logging
import sys
import os
import django
import signal
import datetime

# Set up Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pronto_shoes.settings')
django.setup()

from django.utils import timezone
from django.db import connection
from sincronizacion.tasks import verificar_sincronizaciones_automaticas, procesar_cola_sincronizacion
from sincronizacion.cache_manager import cache_manager, refrescar_cache_automatica, detectar_estado_conexion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('sync_scheduler')

# Global flag for graceful shutdown
running = True

def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info("Recibida señal de apagado. Finalizando después del ciclo actual...")
    running = False

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, handle_shutdown)
signal.signal(signal.SIGTERM, handle_shutdown)

def close_db_connections():
    """Close database connections to prevent them from becoming stale"""
    connection.close()
    logger.debug("Conexiones de base de datos cerradas")

def main():
    """Main scheduler loop"""
    logger.info("Iniciando planificador de sincronización...")
    
    check_interval = 60  # Check every 60 seconds by default
    process_interval = 10  # Process queue every 10 seconds
    cache_refresh_interval = 30 * 60  # Refresh cache every 30 minutes
    connection_check_interval = 5 * 60  # Check connection every 5 minutes
    
    last_check_time = timezone.now() - datetime.timedelta(minutes=10)  # Force initial check
    last_cache_refresh = timezone.now() - datetime.timedelta(minutes=30)  # Force initial cache refresh
    last_connection_check = timezone.now()
    is_online = detectar_estado_conexion()
    
    # Realizar una carga inicial de caché
    if is_online:
        logger.info("Realizando carga inicial de caché...")
        try:
            refrescar_cache_automatica()
            logger.info("Carga inicial de caché completada")
        except Exception as e:
            logger.error(f"Error en carga inicial de caché: {e}")
    
    try:
        while running:
            current_time = timezone.now()
            
            # Verificar estado de conexión periódicamente
            if (current_time - last_connection_check).total_seconds() >= connection_check_interval:
                prev_status = is_online
                is_online = detectar_estado_conexion()
                last_connection_check = current_time
                
                # Si el estado cambió, registrarlo
                if prev_status != is_online:
                    if is_online:
                        logger.info("Conexión recuperada - Cambiando a modo online")
                        # Al volver a modo online, actualizar caché
                        try:
                            refrescar_cache_automatica()
                        except Exception as e:
                            logger.error(f"Error al actualizar caché después de recuperar conexión: {e}")
                    else:
                        logger.info("Conexión perdida - Cambiando a modo offline")
            
            # Refrescar caché periódicamente cuando estamos online
            if is_online and (current_time - last_cache_refresh).total_seconds() >= cache_refresh_interval:
                logger.info("Refrescando caché automáticamente...")
                try:
                    refrescar_cache_automatica()
                    last_cache_refresh = current_time
                except Exception as e:
                    logger.error(f"Error al refrescar caché: {e}")
            
            # Check configurations periodically when online
            if is_online and (current_time - last_check_time).total_seconds() >= check_interval:
                logger.info("Verificando sincronizaciones automáticas programadas...")
                try:
                    verificar_sincronizaciones_automaticas()
                    last_check_time = current_time
                except Exception as e:
                    logger.error(f"Error al verificar sincronizaciones: {e}")
                
                # Close DB connections to prevent them from becoming stale
                close_db_connections()
            
            # Process queue more frequently when online
            if is_online:
                logger.info("Procesando cola de sincronización...")
                try:
                    exitosas, fallidas, conflictos = procesar_cola_sincronizacion(max_items=10)
                    if exitosas + fallidas + conflictos > 0:
                        logger.info(f"Procesadas: {exitosas + fallidas + conflictos} operaciones " 
                                   f"(Exitosas: {exitosas}, Fallidas: {fallidas}, Conflictos: {conflictos})")
                except Exception as e:
                    logger.error(f"Error al procesar cola: {e}")
                
                # Close DB connections to prevent them from becoming stale
                close_db_connections()
            
            # Sleep for a while before next check
            logger.debug(f"Esperando {process_interval} segundos para el próximo ciclo...")
            for _ in range(process_interval):
                if not running:
                    break
                time.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("Planificador interrumpido manualmente")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
    finally:
        logger.info("Planificador de sincronización finalizado")
        close_db_connections()

if __name__ == "__main__":
    main()
