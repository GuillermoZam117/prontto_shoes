from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

app_name = 'requisiciones'

urlpatterns = [
    # Frontend URLs
    path('', login_required(views.requisicion_list), name='lista'),
    path('nueva/', login_required(views.requisicion_create), name='nueva'),
    path('<int:pk>/', login_required(views.requisicion_detail), name='detalle'),
    path('<int:pk>/editar/', login_required(views.requisicion_edit), name='editar'),
    path('reporte/', login_required(views.requisicion_report), name='reporte'),
] 