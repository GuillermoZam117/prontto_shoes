# Plan de Trabajo — Implementación Backend POS Pronto Shoes

## Objetivo
Dejar el backend al 100% según la documentación y requerimientos funcionales.

---

## Orden de Ejecución y Checklist

### 1. Reportes avanzados
- [x] Clientes sin movimientos en un periodo
- [x] Apartados por cliente
- [x] Devoluciones por cliente (motivo, tipo, estado validación)
- [ ] Pedidos surtidos y pendientes
- [ ] Historial de cambios de precios
- [ ] Inventario diario y traspasos
- [ ] Descuentos aplicados por mes
- [ ] Cumplimiento de metas del tabulador

### 2. Reglas de negocio críticas
- [ ] Validar precios > 0
- [ ] Anticipo obligatorio para productos sin devolución
- [ ] Validación de proveedor para devoluciones por defecto
- [ ] Aplicación automática y recálculo manual de descuentos
- [ ] Cálculo de descuentos solo sobre compras pagadas
- [ ] Visibilidad de descuentos y acumulados en tickets
- [ ] Prevención de pedidos duplicados

### 3. Seguridad y administración
- [ ] Fortalecer roles/permisos
- [ ] Implementar 2FA para usuarios críticos
- [ ] Mejorar logs de auditoría
- [ ] Cifrado de datos sensibles

### 4. Sincronización y auditoría
- [ ] Revisar endpoints y logs de sincronización
- [ ] Resolución de conflictos y trazabilidad

### 5. Pruebas y documentación
- [ ] Pruebas automáticas para flujos y reglas clave
- [ ] Documentar cada reporte y regla según plantilla

---

## Detalle de cada paso

Cada avance debe:
- Incluir referencia de archivo y endpoint modificado/creado.
- Documentar la lógica implementada y sus parámetros.
- Dejar evidencia de pruebas (manuales o automáticas).
- Marcar el checklist correspondiente.

---

> Actualiza este documento conforme avances para mantener el foco y la trazabilidad del proyecto.
