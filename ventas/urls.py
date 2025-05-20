from django.urls import path
from . import views

app_name = 'ventas'

urlpatterns = [
    path('', views.pedidos_view, name='lista'),
    path('pos/', views.pos_view, name='pos'),
    path('pedidos/', views.pedidos_view, name='pedidos'),
    path('pedido/<int:pk>/', views.pedido_detail_view, name='detalle_pedido'),
    path('pedido/nuevo/', views.pedido_create_view, name='nuevo_pedido'),
] 