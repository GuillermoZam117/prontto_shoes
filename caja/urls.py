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
    path('facturas/', login_required(views.factura_list), name='facturas'),
    path('reporte/', login_required(views.reporte_caja), name='reporte'),
] 