from django.urls import re_path
from .websocket import SincronizacionConsumer

websocket_urlpatterns = [
    re_path(r'ws/sincronizacion/$', SincronizacionConsumer.as_asgi()),
    re_path(r'ws/sincronizacion/(?P<tienda_id>[^/]+)/$', SincronizacionConsumer.as_asgi()),
]
