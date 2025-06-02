"""
URLs para el sistema de pedidos avanzados
Sistema POS Pronto Shoes
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .viewsets import (
    OrdenClienteViewSet, EstadoProductoSeguimientoViewSet, EntregaParcialViewSet,
    NotaCreditoViewSet, PortalClientePoliticaViewSet, ProductoCompartirViewSet
)

app_name = 'pedidos_avanzados'

# API Router para ViewSets
router = DefaultRouter()
router.register(r'ordenes-cliente', OrdenClienteViewSet, basename='orden-cliente')
router.register(r'seguimiento-productos', EstadoProductoSeguimientoViewSet, basename='seguimiento-producto')
router.register(r'entregas-parciales', EntregaParcialViewSet, basename='entrega-parcial')
router.register(r'notas-credito', NotaCreditoViewSet, basename='nota-credito')
router.register(r'portal-politicas', PortalClientePoliticaViewSet, basename='portal-politica')
router.register(r'productos-compartir', ProductoCompartirViewSet, basename='producto-compartir')

"""
URLs para el sistema de pedidos avanzados
Sistema POS Pronto Shoes
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .viewsets import (
    OrdenClienteViewSet, EstadoProductoSeguimientoViewSet, EntregaParcialViewSet,
    NotaCreditoViewSet, PortalClientePoliticaViewSet, ProductoCompartirViewSet
)

app_name = 'pedidos_avanzados'

# API Router para ViewSets
router = DefaultRouter()
router.register(r'ordenes-cliente', OrdenClienteViewSet, basename='orden-cliente')
router.register(r'seguimiento-productos', EstadoProductoSeguimientoViewSet, basename='seguimiento-producto')
router.register(r'entregas-parciales', EntregaParcialViewSet, basename='entrega-parcial')
router.register(r'notas-credito', NotaCreditoViewSet, basename='nota-credito')
router.register(r'portal-politicas', PortalClientePoliticaViewSet, basename='portal-politica')
router.register(r'productos-compartir', ProductoCompartirViewSet, basename='producto-compartir')

urlpatterns = [
    # API URLs - Incluir todas las rutas del router
    path('api/', include(router.urls)),
    
    # Frontend URLs - Vistas HTML para el POS
    path('', views.dashboard_pedidos_avanzados, name='dashboard'),
    path('grilla/', views.grilla_ordenes_multiple, name='grilla_ordenes'),
    path('orden/<int:orden_id>/', views.detalle_orden_cliente, name='detalle_orden'),
    path('crear/', views.crear_orden_desde_pedidos, name='crear_orden'),
    path('entregas/', views.gestionar_entregas_parciales, name='entregas_parciales'),
    path('reportes/', views.reportes_avanzados, name='reportes'),
    
    # Portal del Cliente
    path('portal/', views.portal_cliente_view, name='portal_cliente'),
    path('portal/<int:cliente_id>/', views.portal_cliente_view, name='portal_cliente_detalle'),
    
    # URLs AJAX para funcionalidades dinámicas
    path('ajax/actualizar-estado/', views.ajax_actualizar_estado_orden, name='ajax_actualizar_estado'),
    path('ajax/pedidos-cliente/', views.ajax_obtener_pedidos_cliente, name='ajax_pedidos_cliente'),
]
