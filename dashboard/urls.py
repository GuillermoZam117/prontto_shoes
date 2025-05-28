from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('data/', views.dashboard_data, name='data'),
    path('sidebar-demo/', views.sidebar_demo, name='sidebar_demo'),
]