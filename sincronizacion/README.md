# Módulo de Sincronización

Este módulo implementa la sincronización bidireccional entre múltiples tiendas y el servidor central, permitiendo la operación offline y la resolución de conflictos.

## Características

- **Operación Offline**: Permite operaciones completas sin conexión al servidor central
- **Cola de Sincronización**: Administra operaciones pendientes de sincronizar
- **Resolución de Conflictos**: Interfaz y lógica para manejar conflictos de datos
- **Priorización de Sincronización**: Configura la importancia de cada tipo de dato
- **Seguimiento**: Registro histórico de sincronizaciones
- **Notificaciones en Tiempo Real**: WebSockets para actualizaciones de estado
- **Seguridad y Auditoría**: Registro detallado de operaciones para auditoría
- **Caché Persistente**: Almacenamiento para datos críticos en modo offline

## Componentes Principales

1. **Modelos**:
   - `ColaSincronizacion`: Operaciones pendientes de sincronización
   - `ConfiguracionSincronizacion`: Configuración por tienda
   - `RegistroSincronizacion`: Historial de sincronizaciones
   - `RegistroAuditoria`: Registro de acciones para auditoría de seguridad

2. **API**:
   - `GET/POST /api/sincronizacion/cola/`: Listar y gestionar operaciones pendientes
   - `GET/POST /api/sincronizacion/configuracion/`: Configurar opciones de sincronización
   - `GET /api/sincronizacion/registros/`: Consultar historial de sincronizaciones
   - `GET /api/sincronizacion/auditoria/`: Consultar registros de auditoría
   - `GET/POST /api/sincronizacion/conflictos/`: Detectar y resolver conflictos

3. **Gestión de Cache**:
   - `CacheManager`: Gestiona el almacenamiento local para operaciones offline
   - Persistencia de datos críticos en disco
   - Detección automática de estado de conexión
   - Refresco periódico de datos en caché

4. **Resolución de Conflictos**:
   - `ConflictResolver`: Sistema de detección y resolución de conflictos
   - Múltiples estrategias de resolución configurables
   - Mezcla de datos según reglas por campo
   - Resolución automática y manual

5. **WebSockets**:
   - Notificaciones en tiempo real del estado de sincronización
   - Alertas de conflictos detectados
   - Actualizaciones de la cola de operaciones
   - Indicador de estado de conexión en tiempo real

6. **Seguridad**:
   - Generación y verificación de tokens para autenticación
   - Firma de datos para garantizar integridad
   - Encriptación de datos sensibles
   - Registro detallado de operaciones para auditoría

5. **WebSockets**:
   - `SincronizacionConsumer`: Gestiona conexiones WebSocket
   - Notificaciones en tiempo real sobre estado de sincronización
   - Alertas de conflictos detectados
   - Actualizaciones de cola de operaciones
   - `POST /api/sincronizacion/cola/{id}/procesar/`: Procesar operación específica
   - `POST /api/sincronizacion/cola/{id}/resolver/`: Resolver conflicto
   - `POST /api/sincronizacion/configuracion/{id}/sincronizar_ahora/`: Iniciar sincronización
   - `GET /api/sincronizacion/registros/`: Historial de sincronizaciones

3. **Comandos**:
   - `python manage.py sincronizar`: Procesa la cola de sincronización
   - `python manage.py sincronizar --completa --tienda={id}`: Sincronización completa
   - `python manage.py sincronizar --continuo`: Modo daemon de sincronización

## Configuración

Para activar la sincronización automática, configure el intervalo y las prioridades en el panel de administración bajo "Configuración de Sincronización".

## Resolución de Conflictos

Los conflictos se identifican cuando:
1. Un mismo objeto ha sido modificado en el servidor central y en la tienda local
2. Una operación no puede procesarse por falta de integridad referencial

Para resolver conflictos:
1. Acceda a `/admin/sincronizacion/colasincronizacion/` y filtre por `tiene_conflicto=True`
2. Elija mantener los datos del servidor central o los datos locales
3. Para conflictos complejos, utilice el editor de datos personalizado

## Operación en Caso de Fallo de Conexión

El sistema automáticamente:
1. Almacena todas las operaciones en la cola local
2. Indica al usuario que está trabajando en modo offline
3. Intenta sincronizar cuando se restablece la conexión
4. Solicita intervención en caso de conflictos irresolubles

## Ejemplo de Flujo

1. Cliente realiza compras en tienda sin conexión a internet
2. Vendedor registra venta normalmente en sistema local
3. Sistema coloca operación en cola de sincronización
4. Cuando se restablece conexión, las ventas se sincronizaron automáticamente
5. Si otra tienda vendió el mismo producto (conflicto de inventario), el administrador resuelve manualmente
