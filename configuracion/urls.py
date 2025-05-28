from django.urls import path
from . import views

app_name = 'configuracion'

urlpatterns = [
    # Configuración del negocio
    path('api/configuracion/negocio/', views.configuracion_negocio, name='configuracion_negocio'),
    
    # Manejo de logotipo
    path('api/configuracion/logotipo/', views.logotipo, name='logotipo'),
    
    # Información de contacto
    path('api/configuracion/informacion-contacto/', views.informacion_contacto, name='informacion_contacto'),
    
    # Detalles de impresión
    path('api/configuracion/detalles-impresion/', views.detalles_impresion, name='detalles_impresion'),
    
    # Configuración completa
    path('api/configuracion/completa/', views.configuracion_completa, name='configuracion_completa'),
    
    # Configuración pública (sin autenticación)
    path('api/configuracion/publica/', views.configuracion_publica, name='configuracion_publica'),
]
