# Historias de Usuario - Sistema POS Pronto Shoes

## Módulo: Gestión de Catálogo

**HU-GC001 (Alta):**
Como *administrador de catálogo*,
quiero *importar la información de los catálogos de proveedores desde archivos Excel*,
para *actualizar rápidamente la base de datos de productos con las novedades de cada temporada.*

**HU-GC002 (Alta):**
Como *administrador de catálogo*,
quiero *registrar las propiedades básicas de cada producto (código, marca, modelo, color, propiedad)*,
para *tener una identificación clara y detallada de cada artículo en el sistema.*

**HU-GC003 (Alta):**
Como *administrador de catálogo*,
quiero *registrar las propiedades comerciales de cada producto (costo, precio, número de página)*,
para *gestionar correctamente los precios y facilitar la referencia al catálogo físico/digital.*

**HU-GC004 (Alta):**
Como *administrador de catálogo*,
quiero *registrar la temporada a la que pertenece un producto y si está en oferta*,
para *poder filtrar y aplicar promociones específicas según la temporada.*

**HU-GC005 (Alta):**
Como *administrador de catálogo*,
quiero *marcar si un producto específico admite devoluciones*,
para *informar correctamente las políticas de venta y gestionar los anticipos requeridos.*

## Módulo: Gestión de Clientes

**HU-CLI001 (Alta):**
Como *personal de ventas* o *administrador*,
quiero *registrar y mantener actualizada la información de las distribuidoras (clientes)*,
para *tener un directorio centralizado y poder gestionar la relación comercial.*

**HU-CLI002 (Media):**
Como *personal de ventas* o *administrador*,
quiero *añadir observaciones relevantes a la ficha de cada cliente*,
para *tener un historial o notas importantes sobre la relación con la distribuidora.*

**HU-CLI003 (Alta):**
Como *personal de caja* o *administrador*,
quiero *registrar los anticipos realizados por los clientes*,
para *llevar un control de los pagos parciales y aplicarlos a futuras compras.*

**HU-CLI004 (Alta):**
Como *personal de caja* o *administrador*,
quiero *gestionar un saldo a favor (nota de crédito) para cada cliente*,
para *poder aplicar créditos por devoluciones o pagos en exceso a sus compras.*

## Módulo: Gestión de Proveedores

**HU-PROV001 (Alta):**
Como *administrador de compras*,
quiero *mantener un catálogo actualizado de los proveedores*,
para *tener la información de contacto y comercial necesaria para realizar pedidos.*

**HU-PROV002 (Alta):**
Como *administrador de compras*,
quiero *marcar si un proveedor requiere un anticipo para procesar los pedidos*,
para *gestionar adecuadamente los pagos y la planificación financiera de las compras.*

**HU-PROV003 (Alta):**
Como *personal de tienda* o *administrador de compras*,
quiero *generar y gestionar los pedidos a los proveedores desde mi tienda*,
para *abastecer el inventario según las necesidades locales.*

## Módulo: Pedidos y Ventas

**HU-PV001 (Alta):**
Como *personal de ventas* o *distribuidora (online)*,
quiero *registrar los pedidos iniciales o apartados de productos*,
para *reservar la mercancía antes de la confirmación final o el pago.*

**HU-PV002 (Alta):**
Como *personal de tienda* o *administrador de compras*,
quiero *generar pedidos a los proveedores basados en los pedidos de los clientes o en las necesidades de stock*,
para *asegurar el abastecimiento de la mercancía solicitada.*

**HU-PV003 (Alta):**
Como *desarrollador* o *administrador del sistema*,
quiero *implementar una validación que evite registrar dos veces el mismo pedido para un cliente y ticket específico*,
para *garantizar la integridad de los datos y prevenir errores operativos.*

**HU-PV004 (Alta):**
Como *administrador de precios* o *personal de ventas*,
quiero *utilizar diferentes listas de precios según la temporada, tipo de cliente u ofertas vigentes*,
para *aplicar las tarifas correctas en cada transacción.*

**HU-PV005 (Media):**
Como *administrador del sistema*,
quiero *configurar si el proceso de surtido (pedido a proveedor) se activa automáticamente después de una venta sin stock*,
para *adaptar el flujo de trabajo a las necesidades operativas.*

## Módulo: Inventario y Almacén

**HU-INV001 (Alta):**
Como *gerente de tienda* o *administrador*,
quiero *consultar el inventario disponible en mi tienda y el inventario consolidado de todas las tiendas*,
para *tener visibilidad completa de la disponibilidad de productos.*

**HU-INV002 (Alta):**
Como *personal de almacén* o *gerente de tienda*,
quiero *gestionar los traspasos de mercancía entre tiendas y almacenes*,
para *distribuir eficientemente el stock según la demanda.*

**HU-INV003 (Media):**
Como *administrador* o *auditor*,
quiero *acceder a un registro histórico diario del inventario (existencias, entradas, salidas)*,
para *realizar análisis, auditorías y seguimiento del movimiento de mercancía.*

## Módulo: Caja y Facturación

**HU-CF001 (Alta):**
Como *personal de caja*,
quiero *registrar todos los ingresos y gastos diarios de mi tienda para calcular el saldo final*,
para *llevar un control preciso del flujo de efectivo diario.*

**HU-CF002 (Media):**
Como *personal de caja* o *administrador*,
quiero *registrar notas de cargo que afecten el flujo de caja*,
para *documentar ajustes o cargos adicionales.*

**HU-CF003 (Media):**
Como *administrador* o *gerente general*,
quiero *consultar el estado de la caja de otras tiendas (con los permisos adecuados)*,
para *tener una visión financiera global del negocio.*

**HU-CF004 (Alta):**
Como *gerente de tienda*,
quiero *un proceso de cancelación de ventas en dos pasos (solicitud y aprobación)*,
para *tener mayor control y seguridad sobre las cancelaciones.*

**HU-CF005 (Alta):**
Como *personal de caja* o *administrador*,
quiero *generar las facturas correspondientes a las ventas realizadas*,
para *cumplir con las obligaciones fiscales y entregar comprobantes a los clientes.*

## Módulo: Devoluciones

**HU-DEV001 (Alta):**
Como *personal de atención al cliente*,
quiero *diferenciar si una devolución es por defecto del producto o por cambio solicitado por el cliente*,
para *aplicar la política correcta y gestionar el proceso adecuadamente.*

**HU-DEV002 (Alta):**
Como *personal de atención al cliente*,
quiero *gestionar el proceso de confirmación con el proveedor para las devoluciones por defecto*,
para *validar si la garantía del proveedor cubre la devolución.*

**HU-DEV003 (Alta):**
Como *personal de atención al cliente* o *administrador*,
quiero *registrar y consultar el estado de todas las devoluciones realizadas*,
para *tener un seguimiento completo del proceso y su resolución.*

**HU-DEV004 (Alta):**
Como *sistema*,
quiero *actualizar automáticamente el inventario y/o el saldo a favor del cliente cuando se acepta una devolución*,
para *mantener la consistencia de los datos en todos los módulos.*

## Módulo: Proceso de Requisiciones en Línea

**HU-REQ001 (Alta):**
Como *distribuidora*,
quiero *poder realizar mis pedidos o requisiciones de productos a través de una interfaz web*,
para *agilizar el proceso y hacerlo desde cualquier lugar.*

**HU-REQ002 (Alta):**
Como *distribuidora*,
quiero *ver la disponibilidad del producto en tiempo real mientras realizo mi pedido en línea*,
para *saber si el producto está en stock o si tendré que esperar.*

**HU-REQ003 (Alta):**
Como *sistema*,
quiero *confirmar el pedido online, actualizar el inventario (apartando el producto) y registrar el pedido*,
para *asegurar la reserva del producto y la correcta gestión del flujo.*

**HU-REQ004 (Alta):**
Como *personal de tienda*,
quiero *recibir una notificación cuando una distribuidora realice un nuevo pedido en línea*,
para *poder procesarlo y prepararlo para el surtido o envío.*

## Módulo: Tabulador de Descuentos por Cliente

**HU-DESC001 (Alta):**
Como *administrador comercial*,
quiero *definir una tabla de descuentos basada en rangos de volumen de compra mensual*,
para *establecer la política de descuentos por lealtad o volumen.*

**HU-DESC002 (Alta):**
Como *sistema*,
quiero *calcular automáticamente el total de compras realizadas por cada cliente durante el mes anterior*,
para *determinar el nivel de descuento aplicable.*

**HU-DESC003 (Alta):**
Como *sistema*,
quiero *aplicar automáticamente el porcentaje de descuento correspondiente a cada cliente al inicio de cada mes*,
para *que las ventas del mes en curso reflejen el descuento ganado.*

## Módulo: Reportes

**HU-REP001 (Media):**
Como *gerente comercial*,
quiero *generar un reporte de clientes sin movimientos en un período determinado*,
para *identificar clientes inactivos y planificar acciones de reactivación.*

**HU-REP002 (Media):**
Como *personal de ventas* o *gerente de tienda*,
quiero *generar un reporte de productos apartados por cliente*,
para *dar seguimiento a las reservas pendientes de pago o entrega.*

**HU-REP003 (Media):**
Como *gerente de tienda* o *administrador*,
quiero *generar un reporte de devoluciones por cliente*,
para *analizar patrones de devolución y la calidad de los productos.*

**HU-REP004 (Media):**
Como *gerente de logística* o *administrador*,
quiero *generar un reporte de pedidos que ya han sido surtidos*,
para *verificar las entregas completadas.*

**HU-REP005 (Media):**
Como *gerente de logística* o *personal de almacén*,
quiero *generar un reporte de pedidos pendientes por surtir*,
para *planificar las tareas de abastecimiento y preparación de pedidos.*

**HU-REP006 (Media):**
Como *administrador* o *auditor*,
quiero *generar un reporte con el historial de cambios de precios de los productos*,
para *tener trazabilidad sobre las modificaciones de precios.*

**HU-REP007 (Media):**
Como *gerente de tienda* o *administrador*,
quiero *generar un reporte del estado del inventario en un día específico*,
para *realizar conciliaciones o análisis puntuales.*

**HU-REP008 (Media):**
Como *personal de ventas* o *gerente de tienda*,
quiero *generar un reporte de la mercancía disponible actualmente en stock*,
para *conocer rápidamente qué productos se pueden ofrecer para venta inmediata.*

## Módulo: Administración y Seguridad

**HU-ADM001 (Alta):**
Como *administrador del sistema*,
quiero *gestionar usuarios, asignar roles y definir permisos específicos para cada rol*,
para *controlar el acceso a las diferentes funcionalidades del sistema según la responsabilidad de cada empleado.*

**HU-ADM002 (Media):**
Como *administrador del sistema* o *auditor*,
quiero *tener acceso a logs de auditoría que registren las operaciones sensibles realizadas en el sistema*,
para *poder rastrear cambios importantes y detectar actividades inusuales.*

## Requisitos No Funcionales (Implícitos en Historias)

*(Estos requisitos se reflejan en cómo se deben implementar las historias anteriores)*

**RNF001 (Alta):** El sistema debe ser desarrollado utilizando el framework Django.
**RNF002 (Alta):** La interfaz de usuario debe ser web y accesible desde navegadores estándar.
**RNF003 (Alta):** El sistema debe asegurar la coordinación y sincronización de datos (inventario, pedidos, caja) entre las diferentes tiendas.
**RNF004 (Media):** La arquitectura del sistema debe considerar la escalabilidad para soportar crecimiento futuro del negocio.

