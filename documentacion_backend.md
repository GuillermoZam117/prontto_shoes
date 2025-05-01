# Documentación Backend — Sistema POS Pronto Shoes

## 1. Tecnologías Seleccionadas

- **Backend:** Django (Python 3.10+)
- **Base de datos:** PostgreSQL (central y local en cada tienda)
- **Sincronización:** APIs REST (Django REST Framework) y/o SymmetricDS
- **Tareas programadas:** Celery o cron
- **Autenticación y permisos:** Sistema de usuarios y grupos de Django

## 2. Arquitectura General

- Cada tienda opera con una instancia local de PostgreSQL y Django.
- El servidor central tiene su propia base de datos PostgreSQL y Django.
- La sincronización de datos se realiza mediante APIs seguras y procesos programados.
- Todos los modelos principales incluyen referencia a la tienda y campos de auditoría (created_at, updated_at, created_by, updated_by).

## 3. Modelos y Tablas Principales

### 3.1. Tienda
- **Tienda**: id, nombre, dirección, contacto, activa, created_at, updated_at

### 3.2. Catálogo de Productos
- **Producto**: id, código (único), marca, modelo, color, propiedad, costo, precio, número de página, temporada, oferta (bool), admite_devolución (bool), proveedor (FK), tienda (FK), created_at, updated_at
- **Proveedor**: id, nombre, contacto, requiere_anticipo (bool), created_at, updated_at

### 3.3. Clientes y Descuentos
- **Cliente**: id, nombre, contacto, observaciones, saldo_a_favor, tienda (FK), created_at, updated_at
- **Anticipo**: id, cliente (FK), monto, fecha, created_at
- **DescuentoCliente**: id, cliente (FK), porcentaje, mes_vigente, monto_acumulado_mes_anterior
- **TabuladorDescuento**: id, rango_min, rango_max, porcentaje

### 3.4. Pedidos y Ventas
- **Pedido**: id, cliente (FK), fecha, estado, total, tienda (FK), tipo, descuento_aplicado, created_at
- **DetallePedido**: id, pedido (FK), producto (FK), cantidad, precio_unitario, subtotal

### 3.5. Inventario y Almacén
- **Inventario**: id, tienda (FK), producto (FK), cantidad_actual, fecha_registro
- **Traspaso**: id, producto (FK), tienda_origen (FK), tienda_destino (FK), cantidad, fecha, estado

### 3.6. Caja y Facturación
- **Caja**: id, tienda (FK), fecha, ingresos, egresos, saldo_final
- **NotaCargo**: id, caja (FK), monto, motivo, fecha
- **Factura**: id, pedido (FK), folio, fecha, total

### 3.7. Devoluciones
- **Devolucion**: id, cliente (FK), producto (FK), tipo (defecto/cambio), motivo, fecha, estado, confirmacion_proveedor (bool), afecta_inventario (bool), saldo_a_favor_generado

### 3.8. Requisiciones en Línea
- **Requisicion**: id, cliente (FK), fecha, estado
- **DetalleRequisicion**: id, requisicion (FK), producto (FK), cantidad

### 3.9. Administración y Seguridad
- **LogAuditoria**: id, usuario (FK), accion, fecha, descripcion
- **Usuarios y Roles**: Usar el sistema de Django para autenticación y permisos.

## 4. Relaciones Clave

- Un producto pertenece a una tienda y a un proveedor.
- Un pedido pertenece a una tienda y a un cliente, y tiene muchos detalles de pedido.
- Inventario y caja están ligados a tienda.
- Traspasos relacionan dos tiendas.
- Devoluciones y anticipos están ligados a clientes y productos.
- Requisiciones y detalles de requisición están ligados a clientes y productos.

## 5. Endpoints Sugeridos (REST API)

- **/api/tiendas/**: CRUD de tiendas
- **/api/productos/**: CRUD de productos, filtrado por tienda, proveedor, temporada, etc.
- **/api/proveedores/**: CRUD de proveedores
- **/api/clientes/**: CRUD de clientes, anticipos, descuentos
- **/api/pedidos/**: CRUD de pedidos y detalles, consulta por estado, tienda, cliente
- **/api/inventario/**: Consulta y actualización de inventario por tienda y producto
- **/api/traspasos/**: Gestión de traspasos entre tiendas
- **/api/caja/**: Registro y consulta de caja, notas de cargo, facturas
- **/api/devoluciones/**: Registro y seguimiento de devoluciones
- **/api/requisiciones/**: Gestión de requisiciones y detalles
- **/api/descuentos/**: Consulta y actualización de tabulador de descuentos
- **/api/logs/**: Consulta de logs de auditoría
- **/api/sincronizacion/**: Endpoints para sincronización de datos entre tiendas y central

## 6. Sincronización de Datos

- Cambios locales se marcan con timestamps y estado de sincronización.
- Al restablecer la conexión, los cambios se envían a la central mediante API.
- El servidor central valida, resuelve conflictos y actualiza la información global.
- Cambios globales (ej. listas de precios) se distribuyen a las tiendas.
- Se mantiene un log de sincronización y auditoría.

## 7. Buenas Prácticas y Consideraciones

- Uso de PostgreSQL por robustez y escalabilidad.
- Campos de auditoría en todos los modelos.
- Validaciones de negocio en modelos y vistas (ej. precios > 0, anticipos obligatorios).
- Soft delete para registros sensibles (is_active o deleted_at).
- Pruebas unitarias y documentación de endpoints.
- Seguridad en APIs y sincronización (autenticación, cifrado, permisos).
- Estrategias de resolución de conflictos en sincronización (timestamps, prioridad central, reglas de negocio).
- Documentar reglas de negocio y flujos críticos.

## 8. Consultas y Estadísticas Centralizadas

- Ventas, inventarios, listas de precios y catálogos pueden consultarse desde la central usando agregaciones y filtros por tienda.
- Endpoints y reportes permiten obtener información consolidada o por tienda.

## 9. Consideraciones para Catálogos de Gran Volumen y Múltiples Proveedores

Para manejar catálogos de 10 proveedores distintos, cada uno con aproximadamente 10,000 productos, se deben aplicar los siguientes ajustes y recomendaciones:

### 9.1. Optimización de Base de Datos
- Crear índices en campos de búsqueda frecuentes: código, proveedor, marca, modelo, temporada.
- Usar claves foráneas y restricciones para mantener integridad referencial.
- Considerar particionar la tabla de productos por proveedor o temporada si el volumen crece más.

### 9.2. Importación Masiva y Actualización
- Implementar procesos de importación masiva (bulk insert/update) usando transacciones para eficiencia y consistencia.
- Utilizar librerías como pandas y openpyxl para procesar archivos Excel grandes.
- Validar y limpiar los datos antes de insertarlos.
- Permitir importaciones incrementales (solo productos nuevos o modificados).

### 9.3. Sincronización Eficiente
- Sincronizar solo los cambios (productos nuevos, modificados o eliminados) usando marcas de tiempo o campos de versión.
- Implementar colas o registros de cambios para evitar transferir todo el catálogo en cada sincronización.

### 9.4. Consultas y Paginación
- Implementar paginación y filtros eficientes en los endpoints de productos.
- Limitar la cantidad de datos retornados por consulta para evitar sobrecargar el sistema y la red.

### 9.5. Escalabilidad y Rendimiento
- Considerar caching para consultas frecuentes de catálogos (ej. Redis).
- Monitorear el rendimiento de las consultas y ajustar los índices según sea necesario.

### 9.6. Manejo de Errores y Logs
- Registrar errores de importación y sincronización para facilitar la depuración.
- Proveer reportes de productos rechazados o inconsistentes.

### 9.7. Documentación y Pruebas
- Documentar los endpoints y procesos de importación/sincronización para grandes volúmenes.
- Realizar pruebas de carga y estrés en la importación y consulta de productos.

## 10. Replicación de Datos y Sincronización entre Tiendas y Base Central

Para garantizar la operación offline de cada tienda y la consolidación de información en la base central, se implementa un esquema de replicación y sincronización de datos. A continuación se detallan los lineamientos y recomendaciones:

### 10.1. Arquitectura de Replicación y Sincronización
- Cada tienda cuenta con una base de datos PostgreSQL local y una instancia de Django.
- El servidor central mantiene la base de datos maestra y su propia instancia de Django.
- La comunicación y sincronización se realiza mediante APIs REST seguras y/o herramientas de replicación como SymmetricDS.

### 10.2. Estrategia de Sincronización
- Los cambios locales (altas, bajas, modificaciones) se marcan con timestamps y un estado de sincronización (pendiente, sincronizado, conflicto).
- Un servicio de sincronización (puede ser un proceso de Django, Celery o cron) detecta los cambios pendientes y los envía a la API central cuando hay conexión.
- El servidor central valida, aplica los cambios y responde con el estado de cada operación (aceptado, rechazado, conflicto).
- Cambios globales (por ejemplo, listas de precios, catálogos) se distribuyen desde la central a las tiendas usando endpoints de descarga o notificaciones push/pull.

### 10.3. Resolución de Conflictos
- Se definen reglas claras para resolver conflictos, por ejemplo:
  - Prioridad a la última actualización (timestamp más reciente).
  - Prioridad a la base central en caso de conflicto crítico.
  - Reglas de negocio específicas para entidades sensibles (ventas, inventario, anticipos).
- Los conflictos se registran en logs y requieren revisión manual si no pueden resolverse automáticamente.

### 10.4. Seguridad y Auditoría
- Toda la comunicación entre tiendas y central debe estar cifrada (HTTPS/TLS).
- Se requiere autenticación y autorización para consumir los endpoints de sincronización.
- Se mantiene un log detallado de todas las operaciones sincronizadas, errores y conflictos.

### 10.5. Herramientas y Tecnologías Sugeridas
- **Django REST Framework**: Para exponer y consumir APIs de sincronización.
- **Celery o cron**: Para tareas programadas de sincronización.
- **SymmetricDS**: Para replicación y sincronización automática de bases de datos PostgreSQL.
- **Mensajería (opcional)**: RabbitMQ, Azure Service Bus, etc., para notificaciones de cambios.

### 10.6. Ejemplo de Flujo de Sincronización
1. La tienda opera normalmente sobre su base local.
2. El servicio de sincronización detecta cambios pendientes (por timestamp o estado).
3. Cuando hay conexión, los cambios se envían a la API central (en lotes o individuales).
4. El servidor central procesa los cambios, resuelve conflictos y actualiza la base maestra.
5. Cambios globales se distribuyen a las tiendas mediante endpoints de descarga o notificaciones.
6. Se registran logs de sincronización y se notifican errores o conflictos.

### 10.7. Consideraciones Adicionales
- Definir la frecuencia de sincronización según la criticidad de los datos (ej. cada 5 minutos, cada hora, manual).
- Implementar mecanismos de reintento y manejo de errores en la sincronización.
- Documentar y probar exhaustivamente los flujos de sincronización y replicación.
- Mantener la documentación actualizada conforme se ajusten los procesos y herramientas.

## Avance de Implementación Backend (Actualizado)

- Modelos, migraciones y administración completados para todas las entidades principales.
- Endpoints REST implementados y funcionales para:
  - Tiendas: /api/tiendas/
  - Productos: /api/productos/
  - Proveedores: /api/proveedores/
  - Clientes: /api/clientes/
  - Anticipos: /api/anticipos/
  - Descuentos de Cliente: /api/descuentos_cliente/
  - Pedidos: /api/pedidos/
  - Detalles de Pedido: /api/detalles_pedido/
  - Inventario: /api/inventario/
  - Traspasos: /api/traspasos/
  - Caja: /api/caja/
  - Notas de Cargo: /api/notas_cargo/
  - Facturas: /api/facturas/
  - Devoluciones: /api/devoluciones/
  - Requisiciones: /api/requisiciones/
  - Detalles de Requisición: /api/detalles_requisicion/
  - Tabulador de Descuentos: /api/tabulador_descuento/
  - Logs de Auditoría: /api/logs_auditoria/
- Serializers y ViewSets creados para todos los modelos anteriores.
- URLs configuradas para exponer los endpoints REST.
- Documentación interactiva de la API disponible en:
  - Swagger: /api/docs/
  - Redoc: /api/redoc/

## Avance de Implementación Backend (Filtros avanzados)

- Filtros avanzados implementados en todos los endpoints principales usando django-filter.
- Ahora es posible realizar búsquedas y filtrados eficientes en la API para todas las entidades clave.
- Documentación interactiva de la API actualizada y funcional en /api/docs/ y /api/redoc/.

Próximos pasos sugeridos:
- Probar los filtros y búsquedas desde Swagger y la interfaz de DRF.
- Implementar autenticación JWT si se requiere seguridad adicional.
- Agregar pruebas automáticas para los endpoints.
- Optimizar permisos, validaciones y performance.

---

Este documento debe mantenerse actualizado conforme avance el desarrollo y se definan detalles específicos de implementación, sincronización y reglas de negocio.
