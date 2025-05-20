/**
 * Sync functionality for Pronto Shoes POS System
 */

// Simplified sync module for the login phase
const ProntoSync = (function() {
    // Configuration
    const config = {
        syncStatusCheckInterval: 60000, // Check sync status every minute
        retryInterval: 30000 // Retry connection every 30 seconds
    };

    // Variables to track sync state
    let syncStatus = 'unknown'; // unknown, connected, disconnected, syncing
    let pendingChanges = 0;
    let lastSyncTime = null;
    
    // Simulated function to check sync status
    function checkSyncStatus() {
        // In a real implementation, this would check connection to the server
        // and determine if there are pending changes to sync
        const online = navigator.onLine;
        
        if (!online) {
            updateSyncStatus('disconnected');
            return;
        }
        
        // For now, we'll just simulate a successful sync
        updateSyncStatus('connected');
        pendingChanges = 0;
        lastSyncTime = new Date();
    }
    
    // Update the sync status indicator in the UI
    function updateSyncStatus(status) {
        syncStatus = status;
        
        // Dispatch event for other components to respond to
        const event = new CustomEvent('sync:statusChanged', { 
            detail: { status, pendingChanges, lastSyncTime }
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
            checkSyncStatus();
        });
        
        window.addEventListener('offline', () => {
            updateSyncStatus('disconnected');
        });
    }
    
    // Return public API
    return {
        init,
        getStatus: () => syncStatus,
        getPendingChanges: () => pendingChanges,
        getLastSyncTime: () => lastSyncTime
    };
})();

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    ProntoSync.init();
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
    }
}; 