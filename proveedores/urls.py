from django.urls import path
from . import views

app_name = 'proveedores'

urlpatterns = [
    path('', views.proveedor_list, name='lista'),
    path('nuevo/', views.proveedor_create, name='nuevo'),
    path('<int:pk>/', views.proveedor_detail, name='detalle'),
    path('<int:pk>/editar/', views.proveedor_edit, name='editar'),
    path('purchase_orders/', views.purchase_order_list, name='purchase_orders'),
    path('purchase_orders/nuevo/', views.purchase_order_create, name='nueva_purchase_order'),
    path('purchase_orders/<int:pk>/', views.purchase_order_detail, name='detalle_purchase_order'),
] 