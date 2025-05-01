# Matriz de Requerimientos - Sistema POS Pronto Shoes

| ID    | Categoría                     | Módulo                        | Requerimiento                                                                 | Prioridad | Fuente                                    |
|-------|-------------------------------|-------------------------------|-------------------------------------------------------------------------------|-----------|-------------------------------------------|
| **Gestión de Catálogo** ||||||
| GC001 | Gestión de Catálogo         | Gestión de Catálogo         | Importar catálogos de proveedores desde archivos Excel.                       | Alta      | 3.1 Gestión de Catálogo                 |
| GC002 | Gestión de Catálogo         | Gestión de Catálogo         | Registrar productos con propiedades: código, marca, modelo, color, propiedad. | Alta      | 3.1 Gestión de Catálogo                 |
| GC003 | Gestión de Catálogo         | Gestión de Catálogo         | Registrar productos con propiedades: costo, precio, número de página.         | Alta      | 3.1 Gestión de Catálogo                 |
| GC004 | Gestión de Catálogo         | Gestión de Catálogo         | Registrar productos con propiedades: temporada, oferta (booleano).            | Alta      | 3.1 Gestión de Catálogo                 |
| GC005 | Gestión de Catálogo         | Gestión de Catálogo         | Marcar si un producto admite devoluciones.                                    | Alta      | 3.1 Gestión de Catálogo                 |
| **Gestión de Clientes** ||||||
| CLI001| Gestión de Clientes         | Gestión de Clientes         | Registrar y mantener base de datos de clientes (distribuidoras).              | Alta      | 3.2 Gestión de Clientes                 |
| CLI002| Gestión de Clientes         | Gestión de Clientes         | Incluir campo de observaciones en el registro de clientes.                    | Media     | 3.2 Gestión de Clientes                 |
| CLI003| Gestión de Clientes         | Gestión de Clientes         | Registrar anticipos realizados por clientes.                                  | Alta      | 3.2 Gestión de Clientes                 |
| CLI004| Gestión de Clientes         | Gestión de Clientes         | Gestionar saldo a favor (nota de crédito) por cliente.                        | Alta      | 3.2 Gestión de Clientes                 |
| CLI005| Gestión de Clientes         | Tabulador de Descuentos     | Calcular y aplicar descuentos automáticamente según volumen de compra mensual. | Alta      | 3.2 / 3.9 Tabulador de Descuentos       |
| **Gestión de Proveedores** ||||||
| PROV001| Gestión de Proveedores      | Gestión de Proveedores      | Mantener catálogo de proveedores actualizado.                                 | Alta      | 3.3 Gestión de Proveedores              |
| PROV002| Gestión de Proveedores      | Gestión de Proveedores      | Marcar si un proveedor requiere anticipo para procesar pedidos.               | Alta      | 3.3 Gestión de Proveedores              |
| PROV003| Gestión de Proveedores      | Gestión de Proveedores      | Permitir a cada tienda generar y gestionar pedidos a proveedores.             | Alta      | 3.3 Gestión de Proveedores              |
| **Pedidos y Ventas** ||||||
| PV001 | Pedidos y Ventas            | Pedidos y Ventas            | Registrar pedidos iniciales (preventivos/apartados) por cliente.              | Alta      | 3.4 Pedidos y Ventas                    |
| PV002 | Pedidos y Ventas            | Pedidos y Ventas            | Generar pedidos a proveedor basados en pedidos de cliente o stock.            | Alta      | 3.4 Pedidos y Ventas                    |
| PV003 | Pedidos y Ventas            | Pedidos y Ventas            | Implementar validación para evitar doble pedido (cliente/ticket).             | Alta      | 3.4 Pedidos y Ventas                    |
| PV004 | Pedidos y Ventas            | Pedidos y Ventas            | Soportar múltiples listas de precios (temporada, cliente, oferta).            | Alta      | 3.4 Pedidos y Ventas                    |
| PV005 | Pedidos y Ventas            | Pedidos y Ventas            | Configurar proceso de surtido opcional post-venta.                          | Media     | 3.4 Pedidos y Ventas                    |
| **Inventario y Almacén** ||||||
| INV001| Inventario y Almacén        | Inventario y Almacén        | Gestionar inventario por tienda y consolidado.                                | Alta      | 3.5 Inventario y Almacén                |
| INV002| Inventario y Almacén        | Inventario y Almacén        | Gestionar traspasos de mercancía entre tiendas/almacenes.                   | Alta      | 3.5 Inventario y Almacén                |
| INV003| Inventario y Almacén        | Inventario y Almacén        | Registrar histórico diario de inventario (existencias, entradas, salidas).    | Media     | 3.5 Inventario y Almacén                |
| **Caja y Facturación** ||||||
| CF001 | Caja y Facturación          | Caja y Facturación          | Registrar flujo de caja diario por tienda (ingresos, gastos, saldo).          | Alta      | 3.6 Caja y Facturación                  |
| CF002 | Caja y Facturación          | Caja y Facturación          | Registrar notas de cargo.                                                     | Media     | 3.6 Caja y Facturación                  |
| CF003 | Caja y Facturación          | Caja y Facturación          | Permitir consulta de caja de otras tiendas (con permisos).                    | Media     | 3.6 Caja y Facturación                  |
| CF004 | Caja y Facturación          | Caja y Facturación          | Implementar proceso de cancelación en 2 pasos (solicitud/aprobación).         | Alta      | 3.6 Caja y Facturación                  |
| CF005 | Caja y Facturación          | Caja y Facturación          | Generar facturas de ventas.                                                   | Alta      | 3.6 Caja y Facturación                  |
| **Devoluciones** ||||||
| DEV001| Devoluciones                | Devoluciones                | Diferenciar tipos de devolución (defecto, cambio).                            | Alta      | 3.7 Devoluciones                      |
| DEV002| Devoluciones                | Devoluciones                | Gestionar confirmación con proveedor para devoluciones por defecto.           | Alta      | 3.7 Devoluciones                      |
| DEV003| Devoluciones                | Devoluciones                | Registrar y seguir estado de las devoluciones.                                | Alta      | 3.7 Devoluciones                      |
| DEV004| Devoluciones                | Devoluciones                | Integrar devoluciones con inventario y saldos de cliente.                     | Alta      | 3.7 Devoluciones                      |
| **Proceso de Requisiciones en Línea** ||||||
| REQ001| Proceso Requisiciones Online| Proceso Requisiciones Online| Permitir a distribuidoras realizar requisiciones/pedidos en línea.            | Alta      | 3.8 Proceso Requisiciones Online        |
| REQ002| Proceso Requisiciones Online| Proceso Requisiciones Online| Validar disponibilidad de producto durante la requisición online.             | Alta      | 3.8 Proceso Requisiciones Online        |
| REQ003| Proceso Requisiciones Online| Proceso Requisiciones Online| Confirmar pedido online y actualizar inventario/apartados.                   | Alta      | 3.8 Proceso Requisiciones Online        |
| REQ004| Proceso Requisiciones Online| Proceso Requisiciones Online| Notificar a tienda sobre nuevos pedidos online.                               | Alta      | 3.8 Proceso Requisiciones Online        |
| **Tabulador de Descuentos** ||||||
| DESC001| Tabulador de Descuentos     | Tabulador de Descuentos     | Definir tabla de descuentos por rangos de compra mensual.                     | Alta      | 3.9 Tabulador de Descuentos           |
| DESC002| Tabulador de Descuentos     | Tabulador de Descuentos     | Calcular automáticamente el total de compras del mes anterior por cliente.    | Alta      | 3.9 Tabulador de Descuentos           |
| DESC003| Tabulador de Descuentos     | Tabulador de Descuentos     | Aplicar el descuento correspondiente al cliente al inicio del mes.            | Alta      | 3.9 Tabulador de Descuentos           |
| **Reportes** ||||||
| REP001| Reportes                    | Gestión de Clientes         | Reporte: Clientes sin movimientos.                                            | Media     | 3.2 Gestión de Clientes / 8. Reportes |
| REP002| Reportes                    | Gestión de Clientes / Inventario | Reporte: Apartados por cliente.                                               | Media     | 3.2 / 3.5 / 8. Reportes               |
| REP003| Reportes                    | Gestión de Clientes / Devoluciones | Reporte: Devoluciones por cliente.                                            | Media     | 3.2 / 3.5 / 8. Reportes               |
| REP004| Reportes                    | Pedidos y Ventas            | Reporte: Pedidos surtidos.                                                    | Media     | 3.4 Pedidos y Ventas / 8. Reportes    |
| REP005| Reportes                    | Pedidos y Ventas            | Reporte: Pedidos por surtir.                                                  | Media     | 3.4 Pedidos y Ventas / 8. Reportes    |
| REP006| Reportes                    | Inventario y Almacén        | Reporte: Cambio de precios.                                                   | Media     | 3.5 Inventario y Almacén / 8. Reportes |
| REP007| Reportes                    | Inventario y Almacén        | Reporte: Inventario por día.                                                  | Media     | 3.5 Inventario y Almacén / 8. Reportes |
| REP008| Reportes                    | Inventario y Almacén        | Reporte: Mercancía disponible.                                                | Media     | 3.5 Inventario y Almacén / 8. Reportes |
| **Administración y Seguridad** ||||||
| ADM001| Administración y Seguridad  | General                       | Gestión de usuarios y roles/permisos.                                         | Alta      | Implícito / 3.6 (Consulta caja)       |
| ADM002| Administración y Seguridad  | General                       | Logs de auditoría para operaciones sensibles.                                 | Media     | Sugerencia 1.2                        |
| **Requisitos No Funcionales** ||||||
| RNF001| Requisitos No Funcionales   | General                       | Sistema desarrollado en Django.                                               | Alta      | 2. Objetivo del Sistema               |
| RNF002| Requisitos No Funcionales   | General                       | Interfaz web accesible.                                                       | Alta      | 2. Objetivo del Sistema               |
| RNF003| Requisitos No Funcionales   | General                       | Coordinación y sincronización entre tiendas.                                  | Alta      | 2. Objetivo del Sistema               |
| RNF004| Requisitos No Funcionales   | General                       | Escalabilidad para futuras necesidades.                                       | Media     | 2. Objetivo del Sistema               |

