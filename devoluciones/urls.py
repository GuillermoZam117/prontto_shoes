from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

app_name = 'devoluciones'

urlpatterns = [
    # Frontend URLs
    path('', login_required(views.devolucion_list), name='lista'),
    path('nueva/', login_required(views.devolucion_create), name='nueva'),
    path('<int:pk>/', login_required(views.devolucion_detail), name='detalle'),
    path('<int:pk>/editar/', login_required(views.devolucion_edit), name='editar'),
    path('<int:pk>/validar/', login_required(views.devolucion_validate), name='validar'),
    path('reporte/', login_required(views.devolucion_report), name='reporte'),
] 