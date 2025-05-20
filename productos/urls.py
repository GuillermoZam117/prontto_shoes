from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('', views.producto_list, name='lista'),
    path('<int:pk>/', views.producto_detail, name='detalle'),
    path('nuevo/', views.producto_create, name='nuevo'),
    path('editar/<int:pk>/', views.producto_edit, name='editar'),
    path('importar/', views.producto_import, name='importar'),
] 