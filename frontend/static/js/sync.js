/**
 * Archivo JavaScript para la gestión de sincronización
 */

document.addEventListener('DOMContentLoaded', function() {
    // Objeto para gestionar la sincronización
    window.SyncManager = {
        // Estado actual de sincronización
        currentStatus: 'unknown',
        
        // Número de operaciones pendientes
        pendingOperations: 0,
        
        // Última sincronización
        lastSync: null,
        
        // Inicializar gestor de sincronización
        init: function() {
            this.checkStatus();
            this.setupEventListeners();
            
            // Comprobar estado cada minuto
            setInterval(() => this.checkStatus(), 60000);
        },
        
        // Verificar estado de sincronización
        checkStatus: function() {
            fetch('/api/sincronizacion/estado/')
                .then(response => response.json())
                .then(data => {
                    this.updateStatus(data);
                })
                .catch(error => {
                    console.error('Error al verificar estado de sincronización:', error);
                    this.setErrorStatus();
                });
        },
        
        // Actualizar estado visual
        updateStatus: function(data) {
            this.currentStatus = data.status;
            this.pendingOperations = data.pending_operations || 0;
            this.lastSync = data.last_sync;
            
            // Actualizar indicador visual
            const statusIndicator = document.getElementById('sync-status-indicator');
            if (statusIndicator) {
                // La actualización se maneja por HTMX, esto es por si falla
                statusIndicator.dataset.status = this.currentStatus;
                statusIndicator.dataset.pending = this.pendingOperations;
            }
            
            // Actualizar pie de página
            const lastSyncTime = document.getElementById('last-sync-time');
            if (lastSyncTime && this.lastSync) {
                lastSyncTime.textContent = this.formatDateTime(this.lastSync);
            }
            
            // Notificar si hay conflictos
            if (this.currentStatus === 'conflict' && data.conflict_count > 0) {
                this.notifyConflict(data.conflict_count);
            }
            
            // Disparar evento personalizado
            document.dispatchEvent(new CustomEvent('sync:statusChanged', {
                detail: {
                    status: this.currentStatus,
                    pendingOperations: this.pendingOperations,
                    lastSync: this.lastSync
                }
            }));
        },
        
        // Establecer estado de error
        setErrorStatus: function() {
            this.currentStatus = 'error';
            
            const statusIndicator = document.getElementById('sync-status-indicator');
            if (statusIndicator) {
                statusIndicator.dataset.status = 'error';
            }
            
            document.dispatchEvent(new CustomEvent('sync:statusChanged', {
                detail: {
                    status: 'error',
                    pendingOperations: this.pendingOperations,
                    lastSync: this.lastSync
                }
            }));
        },
        
        // Configurar escuchadores de eventos
        setupEventListeners: function() {
            // Escuchar eventos de red
            window.addEventListener('online', () => {
                this.checkStatus();
                this.showOnlineNotification();
            });
            
            window.addEventListener('offline', () => {
                this.setErrorStatus();
                this.showOfflineNotification();
            });
            
            // Escuchar eventos de sincronización forzada
            document.addEventListener('sync:forceSynchronization', () => {
                this.forceSynchronization();
            });
        },
        
        // Forzar sincronización
        forceSynchronization: function() {
            fetch('/api/sincronizacion/manual/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.ProntoApp.notify(
                        'Sincronización iniciada', 
                        'El proceso de sincronización ha sido iniciado correctamente.', 
                        'success'
                    );
                    
                    setTimeout(() => this.checkStatus(), 2000);
                } else {
                    window.ProntoApp.notify(
                        'Error', 
                        data.error || 'No se pudo iniciar la sincronización.', 
                        'error'
                    );
                }
            })
            .catch(error => {
                console.error('Error al forzar sincronización:', error);
                window.ProntoApp.notify(
                    'Error', 
                    'No se pudo iniciar la sincronización. Compruebe su conexión.', 
                    'error'
                );
            });
        },
        
        // Notificar conflicto
        notifyConflict: function(count) {
            window.ProntoApp.notify(
                'Conflicto detectado',
                `Se han detectado ${count} conflictos que requieren resolución manual.`,
                'warning'
            );
        },
        
        // Mostrar notificación de conexión
        showOnlineNotification: function() {
            window.ProntoApp.notify(
                'Conexión restablecida',
                'Su dispositivo está conectado nuevamente.',
                'success'
            );
        },
        
        // Mostrar notificación de desconexión
        showOfflineNotification: function() {
            window.ProntoApp.notify(
                'Sin conexión',
                'El dispositivo está offline. Los cambios se sincronizarán cuando se restablezca la conexión.',
                'warning'
            );
        },
        
        // Formatear fecha y hora
        formatDateTime: function(dateString) {
            const date = new Date(dateString);
            return date.toLocaleString('es-MX', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        },
        
        // Obtener token CSRF
        getCSRFToken: function() {
            const cookieValue = document.cookie
                .split('; ')
                .find(row => row.startsWith('csrftoken='))
                ?.split('=')[1];
                
            return cookieValue || '';
        }
    };
    
    // Inicializar gestor de sincronización
    if (document.getElementById('sync-status-indicator')) {
        window.SyncManager.init();
    }
}); 