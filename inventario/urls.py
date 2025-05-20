from django.urls import path
from . import views

app_name = 'inventario'

urlpatterns = [
    path('', views.inventario_list, name='lista'),
    path('traspaso/', views.traspaso_list, name='traspasos'),
    path('traspaso/nuevo/', views.traspaso_create, name='nuevo_traspaso'),
    path('traspaso/<int:pk>/', views.traspaso_detail, name='detalle_traspaso'),
] 