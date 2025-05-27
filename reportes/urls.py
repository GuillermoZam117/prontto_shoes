from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'reportes'

# API Router
router = DefaultRouter()
router.register(r'reportes-personalizados', views.ReportePersonalizadoViewSet)
router.register(r'ejecuciones', views.EjecucionReporteViewSet)

urlpatterns = [
    # Frontend URLs
    path('', views.dashboard_reportes, name='dashboard'),
    path('ejecutar/<str:tipo_reporte>/', views.ejecutar_reporte, name='ejecutar'),
    
    # API URLs
    path('api/', include(router.urls)),
    path('api/avanzados/', views.ReportesAvanzadosAPIView.as_view(), name='api_avanzados'),
]
