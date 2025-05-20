from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('', views.cliente_list, name='lista'),
    path('nuevo/', views.cliente_create, name='nuevo'),
    path('<int:pk>/', views.cliente_detail, name='detalle'),
    path('<int:pk>/editar/', views.cliente_edit, name='editar'),
    path('anticipos/', views.anticipo_list, name='anticipos'),
    path('anticipo/nuevo/', views.anticipo_create, name='nuevo_anticipo'),
    path('descuentos/', views.descuento_list, name='descuentos'),
    path('descuento/nuevo/', views.descuento_create, name='nuevo_descuento'),
] 