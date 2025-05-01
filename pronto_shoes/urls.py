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
from rest_framework import routers, permissions
from tiendas.views import TiendaViewSet
from productos.views import ProductoViewSet
from proveedores.views import ProveedorViewSet
from clientes.views import ClienteViewSet, AnticipoViewSet, DescuentoClienteViewSet
from ventas.views import PedidoViewSet, DetallePedidoViewSet
from inventario.views import InventarioViewSet, TraspasoViewSet
from caja.views import CajaViewSet, NotaCargoViewSet, FacturaViewSet
from devoluciones.views import DevolucionViewSet
from requisiciones.views import RequisicionViewSet, DetalleRequisicionViewSet
from descuentos.views import TabuladorDescuentoViewSet
from administracion.views import LogAuditoriaViewSet
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

router = routers.DefaultRouter()
router.register(r'tiendas', TiendaViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'proveedores', ProveedorViewSet)
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
router.register(r'devoluciones', DevolucionViewSet)
router.register(r'requisiciones', RequisicionViewSet)
router.register(r'detalles_requisicion', DetalleRequisicionViewSet)
router.register(r'tabulador_descuento', TabuladorDescuentoViewSet)
router.register(r'logs_auditoria', LogAuditoriaViewSet)

schema_view = get_schema_view(
    openapi.Info(
        title="POS Pronto Shoes API",
        default_version='v1',
        description="Documentación interactiva de la API del sistema POS Pronto Shoes",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
