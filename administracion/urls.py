from django.urls import path
from . import views

app_name = 'administracion'

urlpatterns = [
    # Dashboard principal de administración
    path('', views.dashboard_admin, name='dashboard'),
    
    # Gestión de usuarios
    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/<int:usuario_id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
    path('usuarios/<int:usuario_id>/cambiar_estado/', views.cambiar_estado_usuario, name='cambiar_estado_usuario'),
    
    # Gestión de grupos y permisos
    path('grupos/', views.lista_grupos, name='lista_grupos'),
    path('grupos/crear/', views.crear_grupo, name='crear_grupo'),
    path('grupos/<int:grupo_id>/editar/', views.editar_grupo, name='editar_grupo'),
    path('grupos/<int:grupo_id>/eliminar/', views.eliminar_grupo, name='eliminar_grupo'),
    
    # Permisos de usuario
    path('usuarios/<int:usuario_id>/permisos/', views.gestionar_permisos_usuario, name='gestionar_permisos_usuario'),
    
    # Auditoría y logs
    path('auditoria/', views.auditoria_dashboard, name='auditoria_dashboard'),
    path('auditoria/logs/', views.logs_auditoria, name='logs_auditoria'),
    path('auditoria/reporte/', views.reporte_auditoria, name='reporte_auditoria'),
    
    # Configuración del sistema
    path('configuracion/', views.configuracion_sistema, name='configuracion_sistema'),
    path('configuracion/backup/', views.backup_sistema, name='backup_sistema'),
    
    # APIs para HTMX/AJAX
    path('api/usuarios/buscar/', views.api_buscar_usuarios, name='api_buscar_usuarios'),
    path('api/logs/filtrar/', views.api_filtrar_logs, name='api_filtrar_logs'),
]
