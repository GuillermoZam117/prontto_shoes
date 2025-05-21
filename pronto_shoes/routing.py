from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
import sincronizacion.routing

application = ProtocolTypeRouter({
    # HTTP requests are handled by Django's standard routing system
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                sincronizacion.routing.websocket_urlpatterns
            )
        )
    ),
})
