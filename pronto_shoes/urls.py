"""
URL configuration for pronto_shoes project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework import routers, permissions
from tiendas.views import TiendaViewSet
from productos.views import ProductoViewSet, CatalogoViewSet
from proveedores.views import ProveedorViewSet, PurchaseOrderViewSet, PurchaseOrderItemViewSet
from clientes.views import ClienteViewSet, AnticipoViewSet, DescuentoClienteViewSet
from ventas.views import PedidoViewSet, DetallePedidoViewSet, ApartadosPorClienteReporteAPIView, PedidosPorSurtirReporteAPIView
from inventario.views import InventarioViewSet, TraspasoViewSet, InventarioActualReporteAPIView
from caja.views import CajaViewSet, NotaCargoViewSet, FacturaViewSet, TransaccionCajaViewSet, MovimientosCajaReporteAPIView
from devoluciones.views import DevolucionViewSet, DevolucionesReporteAPIView
from requisiciones.views import RequisicionViewSet, DetalleRequisicionViewSet, RequisicionesReporteAPIView
from descuentos.views import TabuladorDescuentoViewSet, DescuentosReporteAPIView
from administracion.views import LogAuditoriaViewSet, LogsAuditoriaReporteAPIView
from sincronizacion.views import ColaSincronizacionViewSet, ConfiguracionSincronizacionViewSet, RegistroSincronizacionViewSet, ContentTypeViewSet
from reportes.views import ReportePersonalizadoViewSet, EjecucionReporteViewSet, ReportesAvanzadosAPIView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.contrib.auth import views as auth_views

router = routers.DefaultRouter()
router.register(r'tiendas', TiendaViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'catalogos', CatalogoViewSet)
router.register(r'proveedores', ProveedorViewSet)
router.register(r'purchase_orders', PurchaseOrderViewSet)
router.register(r'purchase_order_items', PurchaseOrderItemViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'anticipos', AnticipoViewSet)
router.register(r'descuentos_cliente', DescuentoClienteViewSet)
router.register(r'pedidos', PedidoViewSet)
router.register(r'detalles_pedido', DetallePedidoViewSet)
router.register(r'inventario', InventarioViewSet)
router.register(r'traspasos', TraspasoViewSet)
router.register(r'caja', CajaViewSet)
router.register(r'notas_cargo', NotaCargoViewSet)
router.register(r'facturas', FacturaViewSet)
router.register(r'transacciones_caja', TransaccionCajaViewSet)
router.register(r'devoluciones', DevolucionViewSet)
router.register(r'requisiciones', RequisicionViewSet)
router.register(r'detalles_requisicion', DetalleRequisicionViewSet)
router.register(r'tabulador_descuento', TabuladorDescuentoViewSet)
router.register(r'logs_auditoria', LogAuditoriaViewSet)
router.register(r'reportes_personalizados', ReportePersonalizadoViewSet)
router.register(r'ejecuciones_reporte', EjecucionReporteViewSet)
router.register(r'sincronizacion/cola', ColaSincronizacionViewSet)
router.register(r'sincronizacion/configuracion', ConfiguracionSincronizacionViewSet)
router.register(r'sincronizacion/registros', RegistroSincronizacionViewSet)
router.register(r'sincronizacion/content-types', ContentTypeViewSet)

urlpatterns = [
    # Redirect root to login page
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('admin/', admin.site.urls),
    # Dashboard application
    path('dashboard/', include('dashboard.urls')),
    # Productos application
    path('productos/', include('productos.urls')),
    # Inventario application
    path('inventario/', include('inventario.urls')),
    # Ventas application
    path('ventas/', include('ventas.urls')),
    # Clientes application
    path('clientes/', include('clientes.urls')),
    # Proveedores application
    path('proveedores/', include('proveedores.urls')),
    # Descuentos application
    path('descuentos/', include('descuentos.urls')),
    # Caja application
    path('caja/', include('caja.urls')),
    # Devoluciones application
    path('devoluciones/', include('devoluciones.urls')),    # Requisiciones application
    path('requisiciones/', include('requisiciones.urls')),
    # Tiendas application
    path('tiendas/', include('tiendas.urls')),    # Sincronizacion application
    path('sincronizacion/', include('sincronizacion.urls')),    # Administracion application
    path('administracion/', include('administracion.urls')),
    # Reportes application
    path('reportes/', include('reportes.urls')),
    path('api/', include(router.urls)),
    path('api/reportes/apartados_por_cliente/', ApartadosPorClienteReporteAPIView.as_view(), name='apartados-por-cliente-reporte'),
    path('api/reportes/pedidos_por_surtir/', PedidosPorSurtirReporteAPIView.as_view(), name='pedidos-por-surtir-reporte'),
    path('api/reportes/inventario_actual/', InventarioActualReporteAPIView.as_view(), name='inventario-actual-reporte'),
    path('api/reportes/movimientos_caja/', MovimientosCajaReporteAPIView.as_view(), name='movimientos-caja-reporte'),
    path('api/reportes/devoluciones/', DevolucionesReporteAPIView.as_view(), name='devoluciones-reporte'),
    path('api/reportes/requisiciones/', RequisicionesReporteAPIView.as_view(), name='requisiciones-reporte'),
    path('api/reportes/descuentos/', DescuentosReporteAPIView.as_view(), name='descuentos-reporte'),
    path('api/reportes/logs_auditoria/', LogsAuditoriaReporteAPIView.as_view(), name='logs-auditoria-reporte'),    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login_simple.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Redirect from Django's default /accounts/login/ to our login page
    path('accounts/login/', RedirectView.as_view(url='/login/', permanent=True), name='accounts_login_redirect'),
]

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
