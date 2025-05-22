from django.urls import path
from . import views

app_name = 'tiendas'

urlpatterns = [
    path('', views.tienda_list, name='lista'),
    path('nueva/', views.tienda_create, name='nueva'),
    path('<int:pk>/', views.tienda_detail, name='detalle'),
    path('<int:pk>/editar/', views.tienda_edit, name='editar'),
    path('<int:pk>/eliminar/', views.tienda_delete, name='eliminar'),
    path('sync/', views.tienda_sync_dashboard, name='sync_dashboard'),
]
