# Guía de Resolución de Problemas - Módulo de Sincronización

Esta guía proporciona soluciones para problemas comunes que pueden surgir durante la operación del módulo de sincronización.

## 1. Problemas de Conexión

### Síntoma: El sistema no detecta correctamente el estado offline/online

**Posibles causas y soluciones:**

1. **Fallo en la detección de conectividad**
   - Verificar la función `detectar_estado_conexion()` en `cache_manager.py`
   - Asegurar que las URL de prueba son accesibles
   - Ajustar los tiempos de timeout en la configuración

2. **Configuración incorrecta de red**
   - Verificar configuración de proxy en el servidor
   - Comprobar reglas de firewall que puedan bloquear la conexión
   - Revisar DNS y resolución de nombres

### Síntoma: Conexión intermitente causa sincronizaciones incompletas

**Solución:**
- Aumentar el número de reintentos en la configuración
- Implementar un mecanismo de backoff exponencial para conexiones inestables
- Verificar el registro para identificar patrones de fallos

## 2. Problemas de Caché

### Síntoma: Datos faltantes en modo offline

**Posibles causas y soluciones:**

1. **Modelos no marcados como críticos**
   - Verificar configuración en `MODELOS_SINCRONIZABLES` en `signals.py`
   - Asegurar que los modelos necesarios tienen `'critico': True`

2. **Caché no actualizada**
   - Ejecutar manualmente `refrescar_cache_automatica()`
   - Verificar que el scheduler está ejecutándose correctamente
   - Comprobar permisos de escritura en directorio de caché

3. **Capacidad de caché insuficiente**
   - Aumentar TTL (tiempo de vida) de la caché
   - Implementar estrategia de LRU (Least Recently Used) para caché limitada
   - Verificar espacio disponible en disco

### Síntoma: Errores al cargar datos desde la caché

**Solución:**
- Verificar integridad de archivos de caché en disco
- Ejecutar limpieza de caché y recreación
- Comprobar permisos de acceso a archivos

## 3. Problemas de Cola de Sincronización

### Síntoma: Operaciones pendientes que no se procesan

**Posibles causas y soluciones:**

1. **Scheduler no ejecutándose**
   - Verificar logs del scheduler
   - Reiniciar el servicio del scheduler
   - Comprobar configuración de CRON o tareas programadas

2. **Operaciones bloqueadas por errores**
   - Revisar operaciones en estado ERROR
   - Verificar `error_mensaje` para diagnóstico
   - Resolver manualmente operaciones problemáticas

3. **Problemas de concurrencia**
   - Verificar bloqueos en la base de datos
   - Ajustar niveles de aislamiento de transacciones
   - Implementar retry lógico para operaciones fallidas

### Síntoma: Alto volumen de operaciones pendientes

**Solución:**
- Aumentar la frecuencia de procesamiento
- Optimizar consultas de sincronización
- Implementar procesamiento por lotes

## 4. Problemas de Resolución de Conflictos

### Síntoma: Conflictos no resueltos automáticamente

**Posibles causas y soluciones:**

1. **Estrategia no configurada**
   - Verificar `estrategias_conflicto` en ConfiguracionSincronizacion
   - Configurar estrategia por defecto en settings

2. **Conflictos complejos**
   - Utilizar la interfaz manual para resolución
   - Implementar estrategia personalizada para el modelo
   - Revisar lógica de negocio para minimizar conflictos

### Síntoma: Resolución incorrecta de conflictos

**Solución:**
- Verificar prioridades configuradas
- Revisar logs de auditoría para identificar patrones
- Ajustar estrategia para modelos específicos

## 5. Problemas de WebSockets

### Síntoma: No se reciben notificaciones en tiempo real

**Posibles causas y soluciones:**

1. **Servicio ASGI no configurado correctamente**
   - Verificar configuración de Daphne o Uvicorn
   - Comprobar que Channels está instalado y configurado
   - Revisar configuración ASGI en `asgi.py`

2. **Problemas con Redis (si se usa como backend)**
   - Verificar conexión a Redis
   - Comprobar permisos y capacidad
   - Considerar alternativa de backend

3. **Permisos de usuario insuficientes**
   - Verificar que el usuario tiene permisos para recibir notificaciones
   - Revisar lógica de autorización en consumidores WebSocket

### Síntoma: Conexiones WebSocket inestables

**Solución:**
- Implementar reconexión automática en cliente
- Verificar configuración de proxy y timeouts
- Ajustar configuración de heartbeat

## 6. Problemas de Rendimiento

### Síntoma: Sincronización lenta

**Posibles causas y soluciones:**

1. **Alto volumen de datos**
   - Implementar sincronización incremental
   - Optimizar consultas de base de datos
   - Considerar usar señales específicas en lugar de post_save genérico

2. **Operaciones bloqueantes**
   - Mover tareas pesadas a trabajos en segundo plano
   - Implementar procesamiento asíncrono
   - Optimizar serializadores

### Síntoma: Uso excesivo de recursos

**Solución:**
- Limitar tamaño de caché
- Implementar expiración de datos no críticos
- Optimizar serialización/deserialización

## 7. Registros y Depuración

Para identificar la causa raíz de problemas:

1. **Habilitar logging detallado**
   ```python
   # En settings.py
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'handlers': {
           'file': {
               'level': 'DEBUG',
               'class': 'logging.FileHandler',
               'filename': 'debug_sincronizacion.log',
           },
       },
       'loggers': {
           'sincronizacion': {
               'handlers': ['file'],
               'level': 'DEBUG',
               'propagate': True,
           },
       },
   }
   ```

2. **Verificar logs del servidor**
   - Revisar logs de Django
   - Revisar logs del servidor web (Nginx, Apache, etc.)
   - Revisar logs de Redis o backend de channels

3. **Tests de diagnóstico**
   - Ejecutar `python manage.py test sincronizacion` para identificar fallos
   - Usar `python sincronizacion\test_integracion_fijo.py` para pruebas manuales

## 8. Mantenimiento y Optimización

Tareas periódicas recomendadas:

1. **Limpieza de cola**
   - Archivar operaciones antiguas completadas
   - Revisar y resolver operaciones en error
   - Optimizar índices de la base de datos

2. **Optimización de caché**
   - Limpiar caché obsoleta
   - Verificar uso de disco
   - Regenerar caché para modelos críticos

3. **Monitoreo**
   - Implementar alertas para operaciones en error persistentes
   - Monitorear tiempo de sincronización
   - Verificar patrones de uso offline
