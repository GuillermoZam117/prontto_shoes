from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

app_name = 'caja'

urlpatterns = [
    # Frontend URLs
    path('', login_required(views.caja_list), name='lista'),
    path('abrir/', login_required(views.abrir_caja), name='abrir'),
    path('cerrar/<int:pk>/', login_required(views.cerrar_caja), name='cerrar'),
    path('movimientos/', login_required(views.movimientos_list), name='movimientos'),
    path('nota-cargo/nueva/', login_required(views.nota_cargo_create), name='nueva_nota_cargo'),
    
    # Facturación URLs
    path('facturas/', login_required(views.factura_list), name='facturas'),
    path('facturas/nueva/', login_required(views.factura_create), name='nueva_factura'),
    path('facturas/<int:pk>/', login_required(views.factura_detail), name='ver_factura'),
    path('facturas/<int:pk>/imprimir/', login_required(views.factura_print), name='imprimir_factura'),
    path('facturas/<int:pk>/pdf/', login_required(views.factura_pdf), name='descargar_factura_pdf'),
    
    path('reporte/', login_required(views.reporte_caja), name='reporte'),
]