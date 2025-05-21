from django.apps import AppConfig


class SincronizacionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sincronizacion'
    verbose_name = 'Sincronización y Operación Offline'
    
    def ready(self):
        import sincronizacion.signals  # noqa
        
        # Inicializar cache manager
        try:
            from sincronizacion.cache_manager import cache_manager, refrescar_cache_automatica
            import threading
            import time
            
            # Iniciar thread para actualización de caché en segundo plano
            def cache_updater():
                # Esperar 30 segundos para permitir que la aplicación se inicie completamente
                time.sleep(30)
                refrescar_cache_automatica()
            
            # Solo iniciar en el proceso principal (evitar múltiples threads en entorno dev)
            if not self.apps.is_installed('django.contrib.admin'):
                threading.Thread(target=cache_updater, daemon=True).start()
                
        except ImportError:
            pass
