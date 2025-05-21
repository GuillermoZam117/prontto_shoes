/**
 * Gestor de conexiones WebSocket para sincronización en tiempo real
 * 
 * Este archivo proporciona funcionalidades para establecer conexiones WebSocket
 * y recibir actualizaciones en tiempo real sobre el estado de sincronización.
 */

class SincronizacionWebSocket {
    constructor(options = {}) {
        this.options = {
            reconnectInterval: 5000,
            maxReconnectAttempts: 5,
            ...options
        };
        
        this.socket = null;
        this.reconnectAttempts = 0;
        this.connected = false;
        this.callbacks = {
            onStatusUpdate: [],
            onConflictUpdate: [],
            onQueueUpdate: [],
            onConnect: [],
            onDisconnect: []
        };
    }
    
    connect() {
        // Determinar protocolo (wss para HTTPS, ws para HTTP)
        const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsURL = `${wsProtocol}${window.location.host}/ws/sincronizacion/`;
        
        try {
            this.socket = new WebSocket(wsURL);
            
            this.socket.onopen = (event) => {
                console.log('Conexión WebSocket establecida');
                this.connected = true;
                this.reconnectAttempts = 0;
                
                // Ejecutar callbacks de conexión
                this.callbacks.onConnect.forEach(callback => callback(event));
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (error) {
                    console.error('Error al procesar mensaje WebSocket:', error);
                }
            };
            
            this.socket.onclose = (event) => {
                console.log('Conexión WebSocket cerrada');
                this.connected = false;
                
                // Ejecutar callbacks de desconexión
                this.callbacks.onDisconnect.forEach(callback => callback(event));
                
                // Intentar reconectar
                this.attemptReconnect();
            };
            
            this.socket.onerror = (error) => {
                console.error('Error en conexión WebSocket:', error);
            };
            
        } catch (error) {
            console.error('Error al crear conexión WebSocket:', error);
        }
    }
    
    handleMessage(data) {
        // Procesar mensajes según tipo
        switch (data.type) {
            case 'initial_state':
                // Estado inicial al conectar
                break;
                
            case 'status_update':
                // Actualización de estado de sincronización
                this.callbacks.onStatusUpdate.forEach(callback => callback(data.data));
                break;
                
            case 'conflict_update':
                // Nuevo conflicto o actualización de conflicto
                this.callbacks.onConflictUpdate.forEach(callback => callback(data.data));
                break;
                
            case 'queue_update':
                // Actualización de cola de sincronización
                this.callbacks.onQueueUpdate.forEach(callback => callback(data.data));
                break;
                
            case 'error':
                console.error('Error de WebSocket:', data.message);
                break;
                
            default:
                console.warn('Tipo de mensaje WebSocket desconocido:', data.type);
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
            console.log('Número máximo de intentos de reconexión alcanzado');
            return;
        }
        
        this.reconnectAttempts++;
        
        console.log(`Intentando reconectar (${this.reconnectAttempts}/${this.options.maxReconnectAttempts})...`);
        
        setTimeout(() => {
            this.connect();
        }, this.options.reconnectInterval);
    }
    
    disconnect() {
        if (this.socket && this.connected) {
            this.socket.close();
        }
    }
    
    // Métodos para registrar callbacks
    onStatusUpdate(callback) {
        this.callbacks.onStatusUpdate.push(callback);
    }
    
    onConflictUpdate(callback) {
        this.callbacks.onConflictUpdate.push(callback);
    }
    
    onQueueUpdate(callback) {
        this.callbacks.onQueueUpdate.push(callback);
    }
    
    onConnect(callback) {
        this.callbacks.onConnect.push(callback);
    }
    
    onDisconnect(callback) {
        this.callbacks.onDisconnect.push(callback);
    }
    
    // Métodos para enviar datos al servidor
    sendMessage(action, data = {}) {
        if (!this.connected) {
            console.error('No se puede enviar mensaje: No hay conexión WebSocket');
            return false;
        }
        
        try {
            this.socket.send(JSON.stringify({
                action,
                data
            }));
            return true;
        } catch (error) {
            console.error('Error al enviar mensaje WebSocket:', error);
            return false;
        }
    }
    
    requestStatusUpdate() {
        return this.sendMessage('get_status');
    }
    
    requestConflictsUpdate() {
        return this.sendMessage('get_conflicts');
    }
    
    requestQueueUpdate() {
        return this.sendMessage('get_queue');
    }
}

// Crear una instancia global para usar en todas las páginas
const sincronizacionWS = new SincronizacionWebSocket();

// Iniciar conexión automáticamente en páginas relacionadas con sincronización
document.addEventListener('DOMContentLoaded', function() {
    // Solo conectar en páginas de sincronización
    if (window.location.pathname.startsWith('/sincronizacion/')) {
        sincronizacionWS.connect();
        
        // Ejemplo de uso:
        sincronizacionWS.onStatusUpdate(data => {
            console.log('Actualización de estado:', data);
            
            // Actualizar contadores en dashboard si existen
            if (document.getElementById('contador-pendientes')) {
                document.getElementById('contador-pendientes').textContent = data.pendientes || 0;
            }
        });
        
        sincronizacionWS.onConflictUpdate(data => {
            console.log('Nuevo conflicto:', data);
            
            // Mostrar notificación
            if (typeof mostrarToast === 'function') {
                mostrarToast(`Nuevo conflicto detectado: ${data.mensaje}`, 'warning');
            }
        });
    }
});

// Función de utilidad para mostrar notificaciones toast
function mostrarToast(mensaje, tipo = 'info') {
    // Verificar si existe la librería Toast de Bootstrap
    if (typeof bootstrap !== 'undefined' && typeof bootstrap.Toast !== 'undefined') {
        // Crear el elemento toast si no existe
        let toastContainer = document.querySelector('.toast-container');
        
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Crear toast
        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${tipo} border-0`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${mensaje}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Cerrar"></button>
            </div>
        `;
        
        toastContainer.appendChild(toastEl);
        
        // Mostrar toast
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
        
        // Eliminar después de mostrarse
        toastEl.addEventListener('hidden.bs.toast', function () {
            toastEl.remove();
        });
    } else {
        // Fallback a console si no hay Bootstrap
        console.log(`[${tipo.toUpperCase()}] ${mensaje}`);
    }
}
