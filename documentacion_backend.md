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
- **Pedido**: id, cliente (FK), fecha, estado, total, tienda (FK), tipo, descuento_aplicado, created_at, updated_at
- **DetallePedido**: id, pedido (FK), producto (FK), cantidad, precio_unitario, subtotal

### 3.5. Inventario y Almacén
- **Inventario**: id, tienda (FK), producto (FK), cantidad_actual, fecha_registro, created_at, updated_at
- **Traspaso**: id, producto (FK), tienda_origen (FK), tienda_destino (FK), cantidad, fecha, estado, created_by

### 3.6. Caja y Facturación
- **Caja**: id, tienda (FK), fecha, ingresos, egresos, saldo_final, created_at, updated_at, created_by, updated_by
- **NotaCargo**: id, caja (FK), monto, motivo, fecha, created_at, created_by
- **Factura**: id, pedido (FK), folio, fecha, total, created_at, created_by

### 3.7. Devoluciones
- **Devolucion**: id, cliente (FK), producto (FK), tipo (defecto/cambio), motivo, fecha, estado, confirmacion_proveedor (bool), afecta_inventario (bool), saldo_a_favor_generado, created_by

### 3.8. Requisiciones en Línea
- **Requisicion**: id, cliente (FK), fecha, estado, created_by
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
- Documentación interactiva de la API actualizada y funcional en /api/docs/ and /api/redoc/.

Próximos pasos sugeridos:
- Probar los filtros y búsquedas desde Swagger y la interfaz de DRF.
- Implementar autenticación JWT si se requiere seguridad adicional.
- Agregar pruebas automáticas para los endpoints.
- Optimizar permisos, validaciones y performance.

## Ejecución y análisis de pruebas automáticas

### ¿Cómo ejecutar todas las pruebas?

1. Abre una terminal en la raíz del proyecto (where `manage.py` is located).
2. Ejecuta el siguiente comando:

   ```bash
   python manage.py test
   ```

3. Django buscará y ejecutará automáticamente todas las pruebas definidas en los archivos `tests.py` of each app.

### ¿Qué esperar como salida?

- Si todas las pruebas pasan, verás una salida similar a:

  ```
  Creating test database for alias 'default'...
  ..........
  ----------------------------------------------------------------------
  Ran XX tests in YYs

  OK
  ```
- If any test fails, you will see details of the error, including:
  - The name of the failed test
  - The reason for the failure (e.g., unexpected status code, validation error, etc.)
  - A traceback for debugging

### ¿Cómo interpretar los resultados?

- **OK**: All tests passed successfully. The backend is working as expected for basic cases.
- **FAIL/ERROR**: Review the error message and traceback. Correct the code or the test as appropriate and re-run the tests.
- **Coverage**: These tests cover creation, listing, and filtering of the main entities. For complete coverage, it is recommended to add tests for updating, deleting, validations, and error cases.

### Buenas prácticas

- Execute tests before each deployment or major change.
- Add new tests when implementing new functionalities or fixing bugs.
- Keep tests and documentation updated.

---

# Guía de Uso de la API: Flujos y Ejemplos

Esta sección describe el flujo típico de uso del sistema POS Pronto Shoes vía API, con ejemplos de requests y responses agrupados por proceso. Así podrás integrar o probar la API fácilmente desde herramientas como Swagger, Postman o código propio.

## 1. Autenticación

La API utiliza autenticación básica (usuario y contraseña de Django) or session. To gain access:
- Enter your credentials in the "Authorize" button of Swagger or send the header `Authorization: Basic <base64(usuario:contraseña)>`.
- If you prefer token authentication, ask the administrator to enable JWT or Token DRF.

## 2. Alta de Cliente

**Endpoint:** `POST /api/clientes/`

**Request ejemplo:**
```json
{
  "nombre": "Zapatería El Paso",
  "contacto": "Juan Pérez",
  "observaciones": "Cliente frecuente",
  "saldo_a_favor": 0,
  "tienda": 1
}
```
**Response ejemplo:**
```json
{
  "id": 5,
  "nombre": "Zapatería El Paso",
  "contacto": "Juan Pérez",
  "observaciones": "Cliente frecuente",
  "saldo_a_favor": "0.00",
  "tienda": 1
}
```

## 3. Creación de Pedido

**Endpoint:** `POST /api/pedidos/`

**Request ejemplo:**
```json
{
  "cliente": 5,
  "fecha": "2025-05-01",
  "estado": "pendiente",
  "total": 1200.00,
  "tienda": 1,
  "tipo": "venta",
  "descuento_aplicado": 0
}
```
**Response ejemplo:**
```json
{
  "id": 10,
  "cliente": 5,
  "fecha": "2025-05-01",
  "estado": "pendiente",
  "total": "1200.00",
  "tienda": 1,
  "tipo": "venta",
  "descuento_aplicado": "0.00"
}
```

## 4. Agregar Detalles a un Pedido

**Endpoint:** `POST /api/detalles_pedido/`

**Request ejemplo:**
```json
{
  "pedido": 10,
  "producto": 3,
  "cantidad": 2,
  "precio_unitario": 600.00,
  "subtotal": 1200.00
}
```
**Response ejemplo:**
```json
{
  "id": 21,
  "pedido": 10,
  "producto": 3,
  "cantidad": 2,
  "precio_unitario": "600.00",
  "subtotal": "1200.00"
}
```

## 5. Registrar Pago (Anticipo)

**Endpoint:** `POST /api/anticipos/`

**Request ejemplo:**
```json
{
  "cliente": 5,
  "monto": 1200.00,
  "fecha": "2025-05-01"
}
```
**Response ejemplo:**
```json
{
  "id": 8,
  "cliente": 5,
  "monto": "1200.00",
  "fecha": "2025-05-01"
}
```

## 6. Registrar Devolución

**Endpoint:** `POST /api/devoluciones/`

**Request ejemplo:**
```json
{
  "cliente": 5,
  "producto": 3,
  "tipo": "defecto",
  "motivo": "Producto dañado",
  "fecha": "2025-05-01",
  "estado": "pendiente",
  "confirmacion_proveedor": false,
  "afecta_inventario": true,
  "saldo_a_favor_generado": 1200.00
}
```
**Response ejemplo:**
```json
{
  "id": 4,
  "cliente": 5,
  "producto": 3,
  "tipo": "defecto",
  "motivo": "Producto dañado",
  "fecha": "2025-05-01",
  "estado": "pendiente",
  "confirmacion_proveedor": false,
  "afecta_inventario": true,
  "saldo_a_favor_generado": "1200.00"
}
```

## 7. Flujo Sugerido de Operación

1. Registrar cliente (if new)
2. Create order and add details
3. Register payment (anticipo)
4. Register return if applicable
5. Consult reports and statuses using the query endpoints (`GET`)

---

**Recommendations:**
- All endpoints require authentication.
- The IDs of customer, product, store, etc., can be consulted with the listing endpoints (`GET /api/clientes/`, `GET /api/productos/`, etc.).
- Use the examples as a basis for your integrations or tests in Swagger/Postman.
- Consult the interactive documentation in `/api/docs/` to see all endpoints and their parameters.

---

# Mejora de la Documentación Interactiva (Swagger)

Para que la documentación de Swagger/Redoc sea clara, útil y muestre ejemplos y agrupación lógica, sigue estas recomendaciones y pasos:

## 1. Instalar drf-yasg (if not installed)

Agrega en tu `requirements.txt`:
```
drf-yasg
```
Luego instala:
```
pip install drf-yasg
```

## 2. Mejora de Serializers y Modelos
- Use `help_text` in model and serializer fields so that Swagger shows descriptions.
- Add docstrings to serializers to explain their purpose.
- Use `extra_kwargs` in Meta for quick examples.

## 3. Ejemplo de Serializer Mejorado
```python
class ClienteSerializer(serializers.ModelSerializer):
    """Serializer for customers. Allows creating, querying, and editing customers."""
    class Meta:
        model = Cliente
        fields = '__all__'
        extra_kwargs = {
            'nombre': {'help_text': 'Full name of the customer', 'example': 'Zapatería El Paso'},
            'contacto': {'help_text': 'Contact person or method', 'example': 'Juan Pérez'},
            'saldo_a_favor': {'help_text': 'Available balance in favor of the customer', 'example': 0},
            'tienda': {'help_text': 'Associated store ID', 'example': 1},
        }
```

## 4. Mejora de ViewSets
- Add docstrings to each ViewSet explaining the process it covers.
- Use decorators like `@swagger_auto_schema` to define request and response examples for each method (requires drf-yasg).
- Customize tags to group endpoints.

## 5. Ejemplo de ViewSet Mejorado
```python
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class ClienteViewSet(viewsets.ModelViewSet):
    """Manages the creation, querying, editing, and filtering of customers."""
    # ...existing code...

    @swagger_auto_schema(
        operation_description="Creates a new customer.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'nombre': openapi.Schema(type=openapi.TYPE_STRING, description='Customer name', example='Zapatería El Paso'),
                'contacto': openapi.Schema(type=openapi.TYPE_STRING, description='Contact', example='Juan Pérez'),
                'saldo_a_favor': openapi.Schema(type=openapi.TYPE_NUMBER, description='Balance in favor', example=0),
                'tienda': openapi.Schema(type=openapi.TYPE_INTEGER, description='Store ID', example=1),
            },
            required=['nombre', 'tienda']
        ),
        responses={201: ClienteSerializer}
    )
    def create(self, request, *args, **kwargs):
        """Creates a new customer and returns it."""
        return super().create(request, *args, **kwargs)
```

## 6. Agrupación de Endpoints
- Use the `tags` attribute in decorators or in the drf-yasg configuration to group endpoints by process (for example: Customers, Orders, Cash).

## 7. Mantener la Documentación
- Every time you add or modify an endpoint, update the docstrings, help_text, and examples.
- Test the documentation in `/api/docs/` and make sure the examples and descriptions are clear.

---

**Following these steps, the interactive documentation will be much more useful and clear for developers and integrators.**

---

Este documento debe mantenerse actualizado conforme avance el desarrollo y se definan detalles específicos de implementación, sincronización y reglas de negocio.

## 11. Procesos Detallados y Reglas de Negocio

### 11.1. Proceso: Importación de Catálogo de Productos

*   **Actor:** Administrador
*   **Inicio:** Se recibe catálogo de proveedor en Excel
*   **Pasos:**
    1.  Administrador accede al módulo de "Catálogo".
    2.  Sube archivo Excel del proveedor.
    3.  El sistema valida formato y estructura.
    4.  El sistema extrae productos y los presenta en vista previa.
    5.  Administrador confirma la importación.
    6.  El sistema guarda los productos con propiedades: marca, modelo, color, talla, temporada, devolución, etc.
    7.  Se marca catálogo como "vigente".
*   **Fin:** Catálogo disponible para requisiciones de distribuidores.

### 11.2. Proceso: Requisición en Línea por Distribuidor

*   **Actor:** Distribuidor
*   **Inicio:** Distribuidor quiere realizar un pedido
*   **Pasos:**
    1.  Distribuidor inicia sesión en el sistema web.
    2.  Accede al catálogo vigente.
    3.  Filtra por marca, modelo, talla, etc.
    4.  Selecciona productos e ingresa cantidades.
    5.  Envía requisición.
    6.  El sistema valida:
        *   Que el producto esté en catálogo vigente.
        *   Que no exista pedido duplicado (cliente + producto).
    7.  El sistema registra pedido como "pendiente por surtir".
*   **Fin:** Pedido queda registrado y visible para administración.

### 11.3. Proceso: Validación y Pedido a Proveedor

*   **Actor:** Administrador
*   **Inicio:** Pedido nuevo por parte del distribuidor
*   **Pasos:**
    1.  Administrador revisa pedidos entrantes.
    2.  Selecciona pedidos para surtir.
    3.  Genera orden de compra para proveedor.
    4.  Marca pedido como "en proceso" o "cancelado".
    5.  Si aplica, el sistema descuenta del inventario.
*   **Fin:** Pedido queda vinculado al proveedor y en estado de seguimiento.

### 11.4. Proceso: Gestión de Inventario y Traspasos

*   **Actor:** Almacén
*   **Inicio:** Movimiento de productos entre tiendas
*   **Pasos:**
    1.  Encargado accede a módulo de inventario.
    2.  Consulta mercancía por tienda o central.
    3.  Crea solicitud de traspaso.
    4.  Confirma traspaso (salida/entrada).
    5.  Productos faltantes / status para validar pedidos incompletos
    6.  El sistema actualiza inventarios por tienda.
    7.  Se genera reporte de movimiento.
*   **Fin:** Inventarios actualizados y trazabilidad asegurada.

### 11.5. Proceso: Flujo de Caja Diario

*   **Actor:** Cajero / Administrador
*   **Inicio:** Inicio de jornada en tienda
*   **Pasos:**
    1.  Cajero abre caja y registra fondo inicial.
    2.  Durante el día registra ventas, anticipos, gastos.
    3.  Al final del día, realiza corte de caja.
    4.  Sistema genera reporte de ingresos y egresos.
    5.  Administrador puede consultar flujo diario de cualquier tienda.
*   **Fin:** Cierre diario de caja con reporte disponible.

### 11.6. Proceso: Aplicación de Descuento por Tabulador

*   **Actor:** Sistema / Administrador
*   **Inicio:** Inicio de mes
*   **Pasos:**
    1.  Sistema consulta ventas acumuladas de cada cliente en el mes anterior.
    2.  Asigna nivel de descuento según tabulador escalonado.
    3.  Aplica el % automáticamente a todos los tickets del mes en curso.
    4.  Muestra en ticket: monto acumulado anterior + % descuento.
    5.  Administrador puede recalcular manualmente si es necesario.
*   **Fin:** Descuento aplicado de forma automática y transparente.

### 11.7. Proceso: Devoluciones de Productos

*   **Actor:** Cliente / Cajero / Administrador
*   **Inicio:** Cliente solicita devolución
*   **Pasos:**
    1.  Cajero recibe solicitud de devolución.
    2.  Identifica tipo de devolución:
        *   Por defecto (garantía)
        *   Por cambio (color/talla)
    3.  El sistema valida si el producto es elegible.
    4.  Valida vigencia de dias de devolucion
    5.  Se confirma con proveedor si aplica (si es por defecto).
    6.  Se genera nota de crédito o anticipo para cliente.
    7.  El inventario se ajusta si el producto regresa.
    8.  Se toma el precio de devolucion que sea menor o igual al monto que el distribuidor.
*   **Fin:** Devolución registrada y reflejada en inventario y saldo del cliente.


### 11.8. Reglas Adicionales y Consideraciones

*   **Devoluciones:**
    *   Vigencia maxima por proveedor.
    *   Vigencia de devolucion por clientes.
    *   Historia de devoluciones.
    *   El precio de devolución tomado será el menor o igual al monto que el distribuidor pagó.

*   **Ofertas y Ajuste de Precios:**
    *   Proceso de oferta de temporada.
    *   Actualizacion de temporada: al activar un nuevo catálogo de temporada, los catálogos de ofertas y de línea anteriores se desactivan.
    *   Proceso de ajuste de precios de temporada.
    *   Validacion de revision si el modelo fue devuelto.
    *   Ajuste de ticket.

*   **Tickets y Pagos:**
    *   Precio de monto recibido.
    *   Nota de credito sobre saldo a favor.
    *   Bloqueo de ticket despues de ajuste.

*   **Programa de Lealtad para Clientes:**
    *   Puntos: definir valor de cada punto.
    *   Definir: monto de compra y cantidad de puntos otorgados.
    *   Los puntos se aplican solo en ventas.
    *   No aplica para devoluciones.

*   **Proceso de Entrada de Mercancía:**
    *   **Costeo:** Al entrar la mercancía, se costea automaticamente de acuerdo al campo de (Descuento de compras en proveedor).
    *   Si se desea, se puede costear manualmente el precio de los artículos.
    *   El costeo manual es por porcentaje (x monto pendiente de confirmar).
    *   Una vez validado el pedido, ya no se puede editar.
    *   Solo un super admin puede editar una entrada por compra a proveedor.

*   **Gestión de Listas de Catálogo:**
    *   Lista temporada - desactivada (implica que un catálogo de temporada específico está inactivo).
    *   Lista oferta - Desactivada (implica que un catálogo de ofertas específico está inactivo).
    *   Lista Temporada 2: al activar un nuevo catálogo de temporada (Lista Temporada 2), los catálogos de ofertas y de línea anteriores se desactivan.
    *   Lista de oferta 2: (proceso para activar un nuevo catálogo de ofertas).

## 12. Resumen de Procesos Documentados

| Módulo / Proceso	| ¿Incluido?	| Comentario |
|---|---|---|
| Importación de Catálogos	| ✅	| Procesado por el administrador |
| Requisición en línea por distribuidor	| ✅	| Flujo completo desde login hasta pedido registrado |
| Validación y generación de pedidos al proveedor	| ✅	| Incluye candado para evitar duplicados |
| Gestión de inventarios y traspasos entre tiendas	| ✅	| Incluye movimientos y trazabilidad |
| Flujo de caja diario	| ✅	| Desde apertura hasta cierre y consultas |
| Aplicación de descuentos por tabulador	| ✅	| Automatizado según reglas de negocio |
| Devoluciones (por defecto o cambio)	| ✅	| Con validación por proveedor incluida |

## 13. Procesos Faltantes o que se pueden agregar como detalle adicional:

| Módulo / Proceso	| Comentario |
|---|---|
| Registro de clientes y saldos	| Puede detallarse el proceso desde el alta del cliente, registro de anticipos y saldo a favor. |
| Facturación	| Aunque está mencionada en "Caja", podríamos hacer un flujo específico para facturación electrónica (si aplica). |
| Control de apartados	| Se mencionan reportes de apartados. Podemos detallar el proceso desde que se aparta mercancía. |
| Cancelaciones	| Se menciona un flujo de cancelación en 2 pasos. Este proceso puede detallarse por separado. |
| Proceso de surtido tras venta	| Hay mención de surtido opcional. Sería útil un flujo para ese caso específico. |
| Reportes y Dashboards	| Aunque no son procesos operativos, podrías definir un proceso de generación, revisión y toma de decisiones. |
