/**
 * Sync functionality for Pronto Shoes POS System
 */

// Simplified sync module for the login phase
const ProntoSync = (function() {
    // Configuration
    const config = {
        syncStatusCheckInterval: 60000, // Check sync status every minute
        retryInterval: 30000, // Retry connection every 30 seconds
        pendingChangesThreshold: 10 // Show warning if more than 10 pending changes
    };

    // Variables to track sync state
    let syncStatus = 'unknown'; // unknown, connected, disconnected, syncing, pendientes, error
    let pendingChanges = 0;
    let conflictsCount = 0;
    let lastSyncTime = null;
    
    // Function to check sync status
    function checkSyncStatus() {
        // First check if the browser is online
        const online = navigator.onLine;
        
        if (!online) {
            updateSyncStatus('disconnected');
            return;
        }
        
        // Call the backend API to check actual sync status
        fetch('/sincronizacion/api/estadisticas/')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error de conexión con el servidor');
                }
                return response.json();
            })
            .then(data => {
                console.log('Sync status data:', data);
                
                // Count pending operations
                let pendingOps = 0;
                data.por_estado.forEach(item => {
                    if (item.estado === 'pendiente') {
                        pendingOps = item.total;
                    }
                });
                
                // Update counters
                pendingChanges = pendingOps;
                conflictsCount = data.conflictos || 0;
                
                // Update UI based on counters
                if (conflictsCount > 0) {
                    updateSyncStatus('conflicto');
                } else if (pendingChanges > 0) {
                    updateSyncStatus('pendientes');
                } else {
                    updateSyncStatus('connected');
                }
                
                // Update additional UI elements
                updateUICounters(pendingChanges, conflictsCount, data.antiguedad_minutos);
                
                // Show notification for conflicts
                if (conflictsCount > 0) {
                    ProntoApp.notify(
                        'Conflictos de Sincronización', 
                        `Hay ${conflictsCount} conflictos que requieren resolución manual.`,
                        'warning'
                    );
                }
                
                // Show warning for old pending changes
                if (data.antiguedad_minutos > 60) { // If older than an hour
                    console.warn('Cambios pendientes antiguos:', data.antiguedad_minutos + ' minutos');
                }
            })
            .catch(error => {
                console.error('Error al verificar estado de sincronización:', error);
                updateSyncStatus('error');
            });
    }
      // Update UI counters and elements
    function updateUICounters(pendingCount, conflictsCount, antiguedadMinutos) {
        // Update pending changes counter
        const contadorPendientes = document.getElementById('contador-pendientes');
        if (contadorPendientes) {
            contadorPendientes.textContent = pendingCount;
            
            // Update visual indicator based on threshold
            if (pendingCount > config.pendingChangesThreshold) {
                contadorPendientes.classList.add('text-warning');
            } else {
                contadorPendientes.classList.remove('text-warning');
            }
        }
        
        // Update conflicts counter
        const contadorConflictos = document.getElementById('contador-conflictos');
        if (contadorConflictos) {
            contadorConflictos.textContent = conflictsCount;
            
            if (conflictsCount > 0) {
                contadorConflictos.classList.add('text-danger');
            } else {
                contadorConflictos.classList.remove('text-danger');
            }
        }
        
        // Update age indicator if available
        const antiguedadIndicator = document.getElementById('antiguedad-cambios');
        if (antiguedadIndicator && antiguedadMinutos) {
            // Format the age
            let formatoAntiguedad = '';
            if (antiguedadMinutos < 60) {
                formatoAntiguedad = Math.round(antiguedadMinutos) + ' minutos';
            } else if (antiguedadMinutos < 1440) { // Less than a day
                formatoAntiguedad = Math.round(antiguedadMinutos / 60) + ' horas';
            } else {
                formatoAntiguedad = Math.round(antiguedadMinutos / 1440) + ' días';
            }
            
            antiguedadIndicator.textContent = formatoAntiguedad;
            
            // Highlight if too old
            if (antiguedadMinutos > 1440) { // Older than a day
                antiguedadIndicator.classList.add('text-danger');
            } else if (antiguedadMinutos > 60) { // Older than an hour
                antiguedadIndicator.classList.add('text-warning');
                antiguedadIndicator.classList.remove('text-danger');
            } else {
                antiguedadIndicator.classList.remove('text-warning', 'text-danger');
            }
        }
    }
    
    // Update the sync status indicator in the UI
    function updateSyncStatus(status) {
        syncStatus = status;
        
        // Dispatch event for other components to respond to
        const event = new CustomEvent('sync:statusChanged', { 
            detail: { status, pendingChanges, lastSyncTime, conflictsCount }
        });
        document.dispatchEvent(event);
    }
      // Initialize the sync system
    function init() {
        // Start periodic sync checks
        setInterval(checkSyncStatus, config.syncStatusCheckInterval);
        
        // Check immediately on load
        setTimeout(checkSyncStatus, 1000);
        
        // Event listener for online/offline events
        window.addEventListener('online', () => {
            console.log('Conexión recuperada. Verificando estado...');
            checkSyncStatus();
        });
        
        window.addEventListener('offline', () => {
            console.log('Conexión perdida.');
            updateSyncStatus('disconnected');
        });
        
        // Setup manual sync button if it exists
        const syncNowButton = document.getElementById('sincronizar-ahora');
        if (syncNowButton) {
            syncNowButton.addEventListener('click', sincronizarAhora);
        }
    }
    
    // Return public API
    return {
        init,
        getStatus: () => syncStatus,
        getPendingChanges: () => pendingChanges,
        getConflictsCount: () => conflictsCount,
        getLastSyncTime: () => lastSyncTime,
        checkNow: checkSyncStatus,
        sincronizarAhora
    };
})();

// Function to manually trigger synchronization
function sincronizarAhora(e) {
    // Prevent default if called from event
    if (e && e.preventDefault) {
        e.preventDefault();
    }
    
    // Show loading indicator
    updateSyncStatus('syncing');
    
    // Get the configuration ID (would be available on the dashboard)
    const configId = document.getElementById('config-id') ? 
        document.getElementById('config-id').value : null;
        
    if (!configId) {
        console.error('No se encontró ID de configuración para sincronización');
        updateSyncStatus('error');
        ProntoApp.notify(
            'Error', 
            'No se pudo iniciar la sincronización: datos incompletos.',
            'error'
        );
        return;
    }
    
    // Call the syncronization endpoint
    fetch(`/sincronizacion/configuracion/${configId}/sincronizar/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error al iniciar sincronización');
        }
        return response.json();
    })
    .then(data => {
        ProntoApp.notify(
            'Sincronización Iniciada', 
            'El proceso de sincronización ha sido iniciado correctamente.',
            'success'
        );
        // Update status and check again in a moment to reflect changes
        setTimeout(checkSyncStatus, 2000);
    })
    .catch(error => {
        console.error('Error al iniciar sincronización:', error);
        updateSyncStatus('error');
        ProntoApp.notify(
            'Error', 
            'No se pudo iniciar la sincronización. Intente nuevamente.',
            'error'
        );
    });
}

// Helper to get CSRF token
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize the synchronization system
    ProntoSync.init();
    
    // Listen for sync status changes
    document.addEventListener('sync:statusChanged', function(e) {
        const { status, pendingChanges, conflictsCount } = e.detail;
        
        // Update status card color and icon
        const statusCard = document.getElementById('estado-conexion-card');
        const statusText = document.getElementById('estado-conexion-texto');
        const statusIcon = document.getElementById('estado-conexion-icono');
        
        if (statusCard && statusText) {
            // Reset classes
            statusCard.className = 'card text-white mb-4';
            
            // Update based on status
            switch(status) {
                case 'connected':
                    statusCard.classList.add('bg-success');
                    statusText.textContent = 'Conectado';
                    if (statusIcon) statusIcon.className = 'fas fa-check-circle me-1';
                    break;
                case 'disconnected':
                    statusCard.classList.add('bg-danger');
                    statusText.textContent = 'Desconectado';
                    if (statusIcon) statusIcon.className = 'fas fa-times-circle me-1';
                    break;
                case 'syncing':
                    statusCard.classList.add('bg-info');
                    statusText.textContent = 'Sincronizando...';
                    if (statusIcon) statusIcon.className = 'fas fa-sync fa-spin me-1';
                    break;
                case 'pendientes':
                    statusCard.classList.add('bg-warning');
                    statusText.textContent = 'Cambios Pendientes';
                    if (statusIcon) statusIcon.className = 'fas fa-exclamation-triangle me-1';
                    break;
                case 'conflicto':
                    statusCard.classList.add('bg-danger');
                    statusText.textContent = 'Conflictos Detectados';
                    if (statusIcon) statusIcon.className = 'fas fa-exclamation-circle me-1';
                    break;
                case 'error':
                    statusCard.classList.add('bg-danger');
                    statusText.textContent = 'Error';
                    if (statusIcon) statusIcon.className = 'fas fa-times-circle me-1';
                    break;
                default:
                    statusCard.classList.add('bg-secondary');
                    statusText.textContent = 'Desconocido';
                    if (statusIcon) statusIcon.className = 'fas fa-question-circle me-1';
            }
        }
        
        // Update sync status indicator in the navbar if exists
        const navbarSyncIndicator = document.getElementById('navbar-sync-indicator');
        if (navbarSyncIndicator) {
            // Remove all existing classes
            navbarSyncIndicator.className = 'sync-status-indicator';
            
            // Add appropriate class based on status
            switch(status) {
                case 'connected':
                    navbarSyncIndicator.classList.add('sync-status-connected');
                    break;
                case 'disconnected':
                    navbarSyncIndicator.classList.add('sync-status-disconnected');
                    break;
                case 'syncing':
                    navbarSyncIndicator.classList.add('sync-status-syncing');
                    break;
                case 'pendientes':
                    navbarSyncIndicator.classList.add('sync-status-pending');
                    break;
                case 'conflicto':
                    navbarSyncIndicator.classList.add('sync-status-error');
                    break;
                case 'error':
                    navbarSyncIndicator.classList.add('sync-status-error');
                    break;
                default:
                    navbarSyncIndicator.classList.add('sync-status-unknown');
            }
        }
        
        // Update sync button state if it exists
        const syncButton = document.getElementById('sincronizar-ahora');
        if (syncButton) {
            if (status === 'syncing') {
                syncButton.disabled = true;
                syncButton.innerHTML = '<i class="fas fa-sync fa-spin me-1"></i> Sincronizando...';
            } else {
                syncButton.disabled = false;
                syncButton.innerHTML = '<i class="fas fa-sync me-1"></i> Sincronizar Ahora';
            }
        }
    });
});

// Global notification system
const ProntoApp = {
    notify: function(title, message, type = 'success') {
        // Use SweetAlert2 if available, otherwise use alert
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: title,
                text: message,
                icon: type,
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000
            });
        } else {
            alert(`${title}: ${message}`);
        }
    },
    
    // Add helper method to show conflict resolution dialog
    showConflictDialog: function(conflictData, onResolve) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: 'Conflicto de Sincronización',
                html: `
                    <div class="text-start">
                        <p>Se ha detectado un conflicto con los datos:</p>
                        <div class="conflict-diff-container">
                            <pre>${JSON.stringify(conflictData, null, 2)}</pre>
                        </div>
                        <p>¿Cómo desea resolver este conflicto?</p>
                    </div>
                `,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Usar datos del servidor',
                cancelButtonText: 'Usar datos locales',
                showDenyButton: true,
                denyButtonText: 'Resolver manualmente',
            }).then((result) => {
                if (result.isConfirmed) {
                    // Server data wins
                    onResolve('servidor');
                } else if (result.isDismissed && result.dismiss === Swal.DismissReason.cancel) {
                    // Local data wins
                    onResolve('local');
                } else if (result.isDenied) {
                    // Manual resolution - redirect to conflict resolution page
                    onResolve('manual');
                }
            });
        } else {
            const decision = confirm('Conflicto detectado. ¿Desea usar los datos del servidor? (Cancelar para usar datos locales)');
            onResolve(decision ? 'servidor' : 'local');
        }
    }
};