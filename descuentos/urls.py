from django.urls import path
from . import views

app_name = 'descuentos'

urlpatterns = [
    path('', views.tabulador_list, name='lista'),
    path('nuevo/', views.tabulador_create, name='nuevo'),
    path('<int:pk>/', views.tabulador_detail, name='detalle'),
    path('<int:pk>/editar/', views.tabulador_edit, name='editar'),
] 