from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Agregar namespace para la aplicación
app_name = 'sincronizacion'

router = DefaultRouter()
router.register(r'cola-sincronizacion', views.ColaSincronizacionViewSet, basename='cola-sincronizacion')
router.register(r'configuracion-sincronizacion', views.ConfiguracionSincronizacionViewSet, basename='configuracion-sincronizacion')
router.register(r'registros-sincronizacion', views.RegistroSincronizacionViewSet, basename='registro-sincronizacion')
router.register(r'content-types', views.ContentTypeViewSet, basename='content-type')
router.register(r'auditoria', views.RegistroAuditoriaViewSet, basename='auditoria')

urlpatterns = [
    # API URLs
    path('api/', include(router.urls)),  # This already includes the estadisticas endpoint through the ViewSet
    path('api/estadisticas/', views.estadisticas_api, name='estadisticas_api'),  # Direct endpoint for frontend
    
    # Frontend URLs
    path('', views.sincronizacion_dashboard, name='sincronizacion_dashboard'),
    path('cola/', views.cola_sincronizacion, name='cola_sincronizacion'),
    path('conflicto/<uuid:operacion_id>/', views.resolver_conflicto, name='resolver_conflicto'),
    path('historial/', views.historial_sincronizacion, name='historial_sincronizacion'),
    path('configuracion/', views.configuracion_sincronizacion, name='configuracion_sincronizacion'),
    path('configuracion/<int:config_id>/sincronizar/', views.sincronizar_ahora, name='sincronizar_ahora'),
    path('auditoria/', views.auditoria_sincronizacion, name='auditoria_sincronizacion'),
    path('offline/', views.offline_status, name='offline_status'),
]
