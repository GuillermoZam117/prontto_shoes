# Frontend - Sistema POS Pronto Shoes

Este directorio contiene la implementación frontend del Sistema POS para Pronto Shoes, desarrollado siguiendo el plan de implementación definido.

## Estructura de Directorios

```
frontend/
├── templates/
│   ├── components/        # Componentes reutilizables
│   │   ├── tables/        # Componentes de tablas
│   │   ├── forms/         # Componentes de formularios
│   │   ├── cards/         # Tarjetas informativas
│   │   ├── modals/        # Modales y diálogos
│   │   ├── navigation/    # Componentes de navegación
│   │   └── sync/          # Indicadores de sincronización
│   ├── layouts/           # Plantillas base
│   ├── partials/          # Fragmentos para HTMX
│   ├── administracion/    # Vistas para módulo de administración
│   ├── caja/              # Vistas para módulo de caja
│   ├── clientes/          # Vistas para módulo de clientes
│   ├── dashboard/         # Vistas para dashboard principal
│   ├── descuentos/        # Vistas para módulo de descuentos
│   ├── devoluciones/      # Vistas para módulo de devoluciones
│   ├── inventario/        # Vistas para módulo de inventario
│   ├── pedidos/           # Vistas para módulo de pedidos
│   ├── productos/         # Vistas para módulo de productos
│   ├── proveedores/       # Vistas para módulo de proveedores
│   ├── reportes/          # Vistas para módulo de reportes
│   ├── requisiciones/     # Vistas para módulo de requisiciones
│   └── sincronizacion/    # Vistas para módulo de sincronización
├── static/
│   ├── css/               # Archivos CSS
│   ├── js/                # Archivos JavaScript
│   ├── img/               # Imágenes y recursos gráficos
│   └── vendor/            # Bibliotecas de terceros
```

## Stack Tecnológico

- **Frontend Base**: Django Templates + Bootstrap 5
- **Interactividad**: HTMX + Alpine.js
- **Formularios**: Django Crispy Forms con Bootstrap 5
- **Tablas**: Django Tables2 para visualización de datos
- **Gráficos**: Chart.js para visualizaciones en reportes
- **Selectores**: Select2 para búsquedas avanzadas
- **Notificaciones**: SweetAlert2 para feedback de usuario
- **Sincronización**: WebSockets para notificaciones en tiempo real

## Componentes Reutilizables

### 1. Sistema de Tablas

Componente para visualizar, filtrar y paginar datos tabulares.

```html
{% include "components/tables/data_table.html" with 
   columns=columns 
   data=data 
   filters=filters 
   actions=actions %}
```

### 2. Sistema de Formularios

Componente para formularios con validación en tiempo real mediante HTMX.

```html
{% include "components/forms/model_form.html" with 
   form=form 
   submit_url=submit_url 
   cancel_url=cancel_url %}
```

### 3. Indicadores de Sincronización

Componente para mostrar el estado de sincronización con la base de datos central.

```html
{% include "components/sync/status_indicator.html" %}
```

## Arquitectura Multisistema y Sincronización

El Sistema POS Pronto Shoes está diseñado para operar en un entorno distribuido con:

1. **Base de Datos Central**:
   - Catálogo principal de productos
   - Configuración global
   - Consolidación de datos

2. **Bases de Datos Locales (Tiendas)**:
   - Replica de datos relevantes
   - Almacenamiento local de transacciones
   - Operación offline completa

El frontend incluye componentes específicos para:
- Visualizar estado de sincronización
- Gestionar operaciones pendientes
- Resolver conflictos de datos
- Mostrar indicadores visuales de estado de conexión

## Desarrollo de Módulos

Cada módulo del sistema tiene sus propias vistas y plantillas en el directorio correspondiente. Los componentes reutilizables garantizan una experiencia de usuario consistente en toda la aplicación.

## Integración con Backend

Todas las vistas consumen APIs RESTful del backend existente, aprovechando HTMX para comunicación asíncrona y Alpine.js para interactividad del lado del cliente.

## Implementación

Consulte el documento `plan_implementacion_frontend.md` para detalles sobre el cronograma de implementación y la estrategia de desarrollo. 