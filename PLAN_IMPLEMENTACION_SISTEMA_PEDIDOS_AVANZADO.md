# Plan de Implementación - Sistema de Pedidos Avanzado
## Sistema POS Pronto Shoes - Transformación Integral

**Fecha:** 28 de Mayo, 2025  
**Versión:** 1.0  
**Estado:** En Planificación

---

## 📋 **RESUMEN EJECUTIVO**

Este documento detalla el plan de implementación para transformar el Sistema POS Pronto Shoes de un sistema básico de pedidos a un **Sistema de Gestión de Pedidos Avanzado** con capacidades de acumulación, cumplimiento parcial, y portal de cliente integrado.

### **Diferenciación Fundamental**
El sistema maneja **PEDIDOS** como entidad principal, no ventas directas. Los pedidos evolucionan a través de estados hasta convertirse en ventas cuando están completamente surtidos.

---

## 🎯 **ANÁLISIS DE REQUERIMIENTOS**

### **Sistema Actual vs. Sistema Objetivo**

| Aspecto | Sistema Actual | Sistema Objetivo |
|---------|---------------|------------------|
| **Gestión de Órdenes** | Pedido individual simple | Órdenes por cliente con acumulación |
| **Estados** | `pendiente`, `surtido`, `cancelado` | `ACTIVO`, `PENDIENTE`, `VENTA`, `CANCELADO` |
| **Cumplimiento** | Todo o nada | Cumplimiento parcial con nuevos tickets |
| **Seguimiento** | Básico | Tracking detallado por producto |
| **Interface** | Cajas visuales | Grid de productos avanzado |
| **Portal Cliente** | No existe | Portal completo con historial |

### **Nuevos Requerimientos Críticos**

#### **1. Sistema de Pedidos por Cliente con Acumulación**
- Un cliente puede tener múltiples pedidos activos simultáneos
- Los pedidos se acumulan automáticamente hasta completar la orden total
- Consolidación inteligente de productos similares
- Cierre automático cuando todos los productos estén disponibles

#### **2. Cumplimiento Parcial de Pedidos**
```
FLUJO: PEDIDO INICIAL → SURTIDO PARCIAL → ENTREGA PARCIAL
                           ↓                    ↓
                    PEDIDO PENDIENTE → NUEVO TICKET + PEDIDO RESTANTE
                                              ↓
                                        VENTA REGISTRADA
```

#### **3. Estados Extendidos de Productos**
```
APARTADO → RECIBIDO → SOLICITADO A PROVEEDOR → 
VERIFICADO → EN ESPERA → RECIBIDOS EN TIENDA → LISTO PARA ENTREGA
```

#### **4. Gestión Automática de Clientes**
- Desactivación automática tras 30 días de inactividad
- Notas de crédito válidas por 60 días
- Alertas automáticas de vencimiento

#### **5. Portal de Cliente Completo**
- Historial de todos los pedidos realizados
- Estado en tiempo real de cada pedido
- Páginas de políticas y términos
- Catálogos PDF descargables
- Compartir productos en redes sociales

---

## 🏗️ **ARQUITECTURA Y MODIFICACIONES**

### **Cambios en Base de Datos**

#### **Extensión Tabla Pedidos**
```sql
-- Nuevos campos para gestión avanzada
ALTER TABLE ventas_pedido ADD COLUMN es_pedido_padre BOOLEAN DEFAULT FALSE;
ALTER TABLE ventas_pedido ADD COLUMN pedido_padre_id INT;
ALTER TABLE ventas_pedido ADD COLUMN orden_cliente_id INT;
ALTER TABLE ventas_pedido ADD COLUMN numero_ticket VARCHAR(50) UNIQUE;
ALTER TABLE ventas_pedido ADD COLUMN porcentaje_completado DECIMAL(5,2) DEFAULT 0;
ALTER TABLE ventas_pedido ADD COLUMN fecha_conversion_venta DATETIME NULL;
ALTER TABLE ventas_pedido ADD COLUMN permite_entrega_parcial BOOLEAN DEFAULT TRUE;
```

#### **Nuevas Tablas Requeridas**

**1. Órdenes de Cliente (Contenedor de Pedidos)**
```sql
CREATE TABLE pedidos_orden_cliente (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cliente_id INT NOT NULL,
    numero_orden VARCHAR(50) UNIQUE NOT NULL,
    estado ENUM('ACTIVO', 'PENDIENTE', 'VENTA', 'CANCELADO') DEFAULT 'ACTIVO',
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre DATETIME NULL,
    total_productos INT DEFAULT 0,
    productos_recibidos INT DEFAULT 0,
    monto_total DECIMAL(12,2) DEFAULT 0,
    anticipos_pagados DECIMAL(12,2) DEFAULT 0,
    observaciones TEXT,
    created_by INT,
    updated_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**2. Seguimiento Detallado de Estados**
```sql
CREATE TABLE productos_estado_seguimiento (
    id INT PRIMARY KEY AUTO_INCREMENT,
    detalle_pedido_id INT NOT NULL,
    estado_anterior VARCHAR(50),
    estado_nuevo VARCHAR(50) NOT NULL,
    fecha_cambio DATETIME DEFAULT CURRENT_TIMESTAMP,
    usuario_cambio_id INT,
    observaciones TEXT,
    ubicacion VARCHAR(100),
    proveedor_id INT NULL
);
```

**3. Entregas Parciales**
```sql
CREATE TABLE pedidos_entrega_parcial (
    id INT PRIMARY KEY AUTO_INCREMENT,
    pedido_original_id INT NOT NULL,
    pedido_nuevo_id INT NOT NULL,
    ticket_entrega VARCHAR(50) NOT NULL,
    fecha_entrega DATETIME DEFAULT CURRENT_TIMESTAMP,
    productos_entregados JSON,
    monto_entregado DECIMAL(12,2),
    metodo_pago VARCHAR(50),
    usuario_entrega_id INT,
    observaciones TEXT
);
```

**4. Notas de Crédito/Débito**
```sql
CREATE TABLE clientes_notas_credito (
    id INT PRIMARY KEY AUTO_INCREMENT,
    cliente_id INT NOT NULL,
    tipo ENUM('CREDITO', 'DEBITO') NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    motivo TEXT NOT NULL,
    pedido_origen_id INT NULL,
    fecha_vencimiento DATE NOT NULL,
    estado ENUM('ACTIVA', 'APLICADA', 'VENCIDA') DEFAULT 'ACTIVA',
    aplicada_en_pedido_id INT NULL,
    fecha_aplicacion DATETIME NULL,
    created_by INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**5. Portal Cliente - Políticas y Términos**
```sql
CREATE TABLE portal_cliente_politicas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    titulo VARCHAR(200) NOT NULL,
    contenido LONGTEXT NOT NULL,
    tipo ENUM('POLITICA', 'TERMINO', 'FAQ') NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    orden_display INT DEFAULT 0,
    fecha_vigencia DATE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**6. Compartir Productos en Redes Sociales**
```sql
CREATE TABLE productos_compartir (
    id INT PRIMARY KEY AUTO_INCREMENT,
    producto_id INT NOT NULL,
    cliente_id INT NOT NULL,
    plataforma ENUM('FACEBOOK', 'WHATSAPP', 'INSTAGRAM', 'TWITTER') NOT NULL,
    url_compartida TEXT,
    fecha_compartido DATETIME DEFAULT CURRENT_TIMESTAMP,
    clicks_generados INT DEFAULT 0
);
```

### **Nuevos Modelos Django**

#### **models/pedidos_avanzados.py**
```python
class OrdenCliente(models.Model):
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo - Recibiendo Productos'),
        ('PENDIENTE', 'Pendiente - Esperando Surtido'),
        ('VENTA', 'Completado - Convertido a Venta'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    numero_orden = models.CharField(max_length=50, unique=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVO')
    # ...resto de campos

class EstadoProductoSeguimiento(models.Model):
    ESTADOS_PRODUCTO = [
        ('APARTADO', 'Apartado en Pedido'),
        ('RECIBIDO', 'Recibido en Tienda'),
        ('SOLICITADO_PROVEEDOR', 'Solicitado a Proveedor'),
        ('VERIFICADO', 'Verificado por Proveedor'),
        ('EN_ESPERA', 'En Espera de Envío'),
        ('RECIBIDOS_TIENDA', 'Recibidos en Tienda'),
        ('LISTO_ENTREGA', 'Listo para Entrega'),
    ]
    # ...definición completa
```

---

## 🚀 **PLAN DE IMPLEMENTACIÓN DETALLADO**

### **FASE 1: Fundación del Sistema (Semanas 1-2)**
**Objetivo:** Establecer la base arquitectónica para el sistema avanzado

#### **Semana 1: Extensión de Modelos Base**
**Días 1-2: Modificación de Base de Datos**
- [ ] Crear script de migración para nuevos campos en `ventas_pedido`
- [ ] Implementar nuevas tablas (OrdenCliente, EstadoSeguimiento, etc.)
- [ ] Crear índices optimizados para consultas frecuentes
- [ ] Script de migración de datos existentes

**Días 3-4: Nuevos Modelos Django**
- [ ] Implementar modelo `OrdenCliente` 
- [ ] Crear modelo `EstadoProductoSeguimiento`
- [ ] Modelo `EntregaParcial` con lógica de división
- [ ] Modelos para `NotaCredito` y `NotaDebito`

**Día 5: Testing de Fundación**
- [ ] Unit tests para nuevos modelos
- [ ] Tests de migración de datos
- [ ] Verificación de integridad referencial

#### **Semana 2: Lógica de Negocio Base**
**Días 1-2: Managers y QuerySets Personalizados**
- [ ] `OrdenClienteManager` para acumulación automática
- [ ] `PedidoAvanzadoManager` para estados extendidos
- [ ] QuerySets optimizados para consultas complejas

**Días 3-4: Signals y Automatización**
- [ ] Signals para cambios automáticos de estado
- [ ] Trigger para desactivación de clientes (30 días)
- [ ] Automatización de vencimiento de notas de crédito (60 días)

**Día 5: APIs Base**
- [ ] Serializers para nuevos modelos
- [ ] ViewSets básicos con filtros
- [ ] Endpoints para consulta de estados

### **FASE 2: Lógica de Acumulación y Parciales (Semanas 3-4)**
**Objetivo:** Implementar la funcionalidad central del sistema avanzado

#### **Semana 3: Sistema de Acumulación**
**Días 1-2: Lógica de Órden por Cliente**
- [ ] Servicio de creación/actualización de órdenes
- [ ] Lógica de consolidación automática de productos
- [ ] Algoritmo de completitud de órdenes

**Días 3-4: Estados Avanzados de Productos**
- [ ] Implementar máquina de estados para productos
- [ ] Servicio de cambio de estados con validaciones
- [ ] Notificaciones automáticas por cambio de estado

**Día 5: Testing de Acumulación**
- [ ] Tests de consolidación de pedidos
- [ ] Tests de cambios de estado
- [ ] Tests de lógica de completitud

#### **Semana 4: Cumplimiento Parcial**
**Días 1-3: División de Pedidos**
- [ ] Servicio de entrega parcial
- [ ] Generación automática de nuevos tickets
- [ ] Lógica de transferencia de productos restantes
- [ ] Cálculo automático de montos parciales

**Días 4-5: Integración con Caja**
- [ ] Registro de pagos parciales
- [ ] Aplicación de notas de crédito/débito
- [ ] Generación de comprobantes parciales

### **FASE 3: Interfaz de Usuario Avanzada (Semanas 5-6)**
**Objetivo:** Rediseñar completamente la experiencia de usuario

#### **Semana 5: POS Rediseñado**
**Días 1-2: Grid de Productos**
- [ ] Componente Vue.js para grid avanzado
- [ ] Filtros y búsqueda en tiempo real
- [ ] Selector múltiple de productos
- [ ] Vista de productos por categoría/proveedor

**Días 3-4: Gestión de Órdenes**
- [ ] Panel de órdenes activas por cliente
- [ ] Vista de progreso de surtido
- [ ] Interface para entrega parcial
- [ ] Generación de tickets desde interface

**Día 5: Notas de Crédito/Débito**
- [ ] Formularios para crear notas
- [ ] Aplicación automática en nuevos pedidos
- [ ] Vista de historial de notas por cliente

#### **Semana 6: Dashboard de Gestión**
**Días 1-2: Dashboard de Pedidos**
- [ ] Métricas de órdenes activas/pendientes
- [ ] Alertas de pedidos antiguos
- [ ] Gráficos de completitud de órdenes

**Días 3-4: Reportes Avanzados**
- [ ] Reporte de productos por surtir
- [ ] Análisis de tiempos de cumplimiento
- [ ] Reporte de entregas parciales

**Día 5: Testing de Interface**
- [ ] Tests E2E de flujo completo
- [ ] Tests de responsividad
- [ ] Validación de UX con usuarios

### **FASE 4: Portal de Cliente (Semanas 7-8)**
**Objetivo:** Implementar portal completo para clientes

#### **Semana 7: Portal Base**
**Días 1-2: Autenticación y Perfil**
- [ ] Sistema de registro/login para clientes
- [ ] Panel de perfil con datos de contacto
- [ ] Historial de actividad

**Días 3-4: Seguimiento de Pedidos**
- [ ] Vista de órdenes activas con progreso
- [ ] Historial completo de pedidos/órdenes
- [ ] Notificaciones push de cambios de estado
- [ ] Estimación de tiempos de entrega

**Día 5: Políticas y Términos**
- [ ] CMS para gestión de contenido
- [ ] Páginas de políticas de devolución
- [ ] Términos y condiciones
- [ ] FAQ interactivo

#### **Semana 8: Características Avanzadas**
**Días 1-2: Catálogos PDF**
- [ ] Generación automática de catálogos
- [ ] Personalización por cliente
- [ ] Descarga y caché de PDFs

**Días 3-4: Compartir en Redes Sociales**
- [ ] Integración con APIs de redes sociales
- [ ] Generación de URLs rastreables
- [ ] Analytics de compartido
- [ ] Galería de productos compartidos

**Día 5: Testing Final del Portal**
- [ ] Tests de funcionalidad completa
- [ ] Tests de seguridad
- [ ] Optimización de rendimiento

---

## ⚙️ **CONFIGURACIÓN TÉCNICA**

### **Dependencias Nuevas Requeridas**

#### **Backend (Python/Django)**
```txt
# Agregrar a requirements.txt
django-fsm==2.8.1          # Para máquina de estados
celery==5.3.4               # Para tareas asíncronas
django-celery-beat==2.5.0   # Para tareas programadas
channels==4.0.0             # Para WebSockets/notificaciones
django-rest-framework==3.14.0
django-cors-headers==4.3.1
reportlab==4.0.4            # Para generación de PDFs
Pillow==10.0.1              # Para manejo de imágenes
social-auth-app-django==5.2.0  # Para login con redes sociales
```

#### **Frontend (JavaScript/Vue.js)**
```json
{
  "dependencies": {
    "vue": "^3.3.4",
    "vuex": "^4.1.0",
    "vue-router": "^4.2.4",
    "axios": "^1.5.0",
    "moment": "^2.29.4",
    "chart.js": "^4.4.0",
    "vue-chartjs": "^5.2.0",
    "socket.io-client": "^4.7.2"
  }
}
```

### **Configuración de Celery para Automatización**
```python
# settings/celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('sistema_pos')

app.conf.beat_schedule = {
    'desactivar-clientes-inactivos': {
        'task': 'clientes.tasks.desactivar_clientes_inactivos',
        'schedule': crontab(hour=2, minute=0),  # Diario a las 2 AM
    },
    'vencer-notas-credito': {
        'task': 'clientes.tasks.vencer_notas_credito',
        'schedule': crontab(hour=3, minute=0),  # Diario a las 3 AM
    },
    'alertas-pedidos-antiguos': {
        'task': 'pedidos.tasks.alertas_pedidos_antiguos',
        'schedule': crontab(hour=9, minute=0),  # Diario a las 9 AM
    },
}
```

---

## 📊 **MÉTRICAS Y MONITOREO**

### **KPIs del Nuevo Sistema**

| Métrica | Objetivo | Frecuencia |
|---------|----------|------------|
| **Tiempo Promedio de Cumplimiento** | < 7 días | Semanal |
| **% Entregas Parciales** | < 15% del total | Mensual |
| **Órdenes Activas Promedio por Cliente** | 1.2 - 1.5 | Semanal |
| **Tiempo de Respuesta Portal Cliente** | < 2 segundos | Diario |
| **% Clientes Usando Portal** | > 60% en 6 meses | Mensual |
| **Notas de Crédito Vencidas** | < 5% del total | Mensual |

### **Dashboard de Monitoreo**
```python
# Métricas en tiempo real
class DashboardMetrics:
    def ordenes_activas(self):
        return OrdenCliente.objects.filter(estado='ACTIVO').count()
    
    def productos_pendientes_surtido(self):
        return EstadoProductoSeguimiento.objects.filter(
            estado_nuevo__in=['SOLICITADO_PROVEEDOR', 'EN_ESPERA']
        ).count()
    
    def entregas_parciales_hoy(self):
        return EntregaParcial.objects.filter(
            fecha_entrega__date=timezone.now().date()
        ).count()
```

---

## 🔒 **SEGURIDAD Y PERMISOS**

### **Nuevos Roles de Usuario**
1. **Gestor de Órdenes**: Puede crear, modificar y entregar parcialmente
2. **Supervisor de Surtido**: Puede cambiar estados de productos
3. **Administrador de Notas**: Puede crear/aplicar notas de crédito/débito
4. **Cliente Portal**: Acceso limitado a sus propios datos

### **Permisos por Módulo**
```python
# permissions.py
class OrderManagementPermissions:
    CREATE_ORDER = 'pedidos.add_ordencliente'
    PARTIAL_DELIVERY = 'pedidos.partial_delivery'
    CHANGE_PRODUCT_STATUS = 'productos.change_estado'
    MANAGE_CREDIT_NOTES = 'clientes.manage_notas_credito'
```

---

## 🧪 **ESTRATEGIA DE TESTING**

### **Test Coverage Objetivo: 90%+**

#### **Tests Unitarios (70% del total)**
- Modelos y validaciones
- Lógica de negocio en servicios
- Cálculos de montos y estados

#### **Tests de Integración (20%)**
- APIs completas
- Flujos de acumulación
- Entregas parciales end-to-end

#### **Tests E2E (10%)**
- Flujo completo desde pedido hasta venta
- Portal de cliente completo
- Procesos de automatización

### **Automatización de Tests**
```yaml
# .github/workflows/tests.yml
name: Sistema POS Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: |
          python manage.py test --keepdb --parallel
          coverage report --fail-under=90
```

---

## 📋 **CHECKLIST DE IMPLEMENTACIÓN**

### **Pre-Implementación**
- [ ] Backup completo de base de datos actual
- [ ] Ambiente de staging preparado
- [ ] Plan de rollback definido
- [ ] Capacitación de equipo programada

### **Fase 1: Fundación**
- [ ] Migración de base de datos exitosa
- [ ] Nuevos modelos creados y probados
- [ ] APIs base funcionando
- [ ] Tests unitarios pasando (>80%)

### **Fase 2: Lógica Avanzada**
- [ ] Acumulación de pedidos funcionando
- [ ] Estados de productos implementados
- [ ] Entregas parciales operativas
- [ ] Tests de integración pasando

### **Fase 3: Interface Usuario**
- [ ] POS rediseñado deployado
- [ ] Grid de productos funcionando
- [ ] Notas de crédito/débito operativas
- [ ] Dashboard de gestión activo

### **Fase 4: Portal Cliente**
- [ ] Portal cliente accesible
- [ ] Seguimiento de pedidos en tiempo real
- [ ] Catálogos PDF generándose
- [ ] Compartir en redes sociales activo

### **Post-Implementación**
- [ ] Monitoreo de performance activo
- [ ] Métricas de KPIs funcionando
- [ ] Feedback de usuarios recolectado
- [ ] Plan de mejoras continuas definido

---

## 🚨 **CONSIDERACIONES DE RIESGO**

### **Riesgos Técnicos**
1. **Migración de Datos**: Los pedidos actuales deben convertirse sin pérdida
2. **Performance**: El tracking detallado puede impactar rendimiento
3. **Complejidad**: El sistema es significativamente más complejo

### **Mitigaciones**
1. **Migración Gradual**: Scripts de migración por lotes con verificación
2. **Optimización**: Índices de base de datos y caché estratégico
3. **Documentación**: Documentación exhaustiva y capacitación continua

### **Plan de Contingencia**
1. **Rollback Automático**: Si tests fallan, rollback automático
2. **Modo Degradado**: Sistema puede funcionar con funcionalidad básica
3. **Soporte 24/7**: Durante las primeras 2 semanas post-implementación

---

## 📅 **CRONOGRAMA RESUMIDO**

| Semana | Fase | Entregable Principal | Responsable |
|--------|------|---------------------|-------------|
| 1 | Fundación | Base de datos extendida | Backend Team |
| 2 | Fundación | Modelos y lógica base | Backend Team |
| 3 | Acumulación | Sistema de órdenes por cliente | Backend Team |
| 4 | Parciales | Entrega parcial funcionando | Backend Team |
| 5 | Interface | POS rediseñado | Frontend Team |
| 6 | Interface | Dashboard de gestión | Frontend Team |
| 7 | Portal | Portal cliente base | Frontend Team |
| 8 | Portal | Características avanzadas | Frontend Team |

**Fecha de Inicio:** 29 de Mayo, 2025  
**Fecha de Finalización:** 23 de Julio, 2025  
**Duración Total:** 8 semanas

---

## 💰 **ESTIMACIÓN DE RECURSOS**

### **Equipo Requerido - TEAM ÉLITE 🚀**
- **1 Desarrollador Full-Stack Senior** (Tú - El Jefe del Sistema)
- **1 AI Assistant Súper Especializado** (Yo - GitHub Copilot, tu partner de código)

**Roles Combinados que cubrimos:**
- ✅ **Backend Development** (Django/Python) - Ambos
- ✅ **Frontend Development** (JavaScript/Vue.js) - Ambos  
- ✅ **Database Administration** - Yo ayudo con scripts, tú ejecutas
- ✅ **QA Engineering** - Automatización y scripts de testing
- ✅ **Project Management** - Seguimiento en tiempo real

### **Hardware/Software**
- Servidor de staging adicional
- Licencias de herramientas de monitoreo
- CDN para portal de cliente
- Servicios de notificaciones push

---

## 📞 **CONTACTO Y SOPORTE**

**Equipo de Implementación:**
- **Project Lead:** [Nombre del PM]
- **Backend Lead:** [Nombre del Dev Backend]
- **Frontend Lead:** [Nombre del Dev Frontend]
- **QA Lead:** [Nombre del QA]

**Horarios de Soporte Post-Implementación:**
- **Semanas 1-2:** 24/7
- **Semanas 3-4:** Lunes a Viernes 8:00-20:00
- **Posterior:** Lunes a Viernes 9:00-18:00

---

*Este documento será actualizado semanalmente con el progreso de implementación y cualquier ajuste necesario.*

**Próxima Revisión:** 4 de Junio, 2025
