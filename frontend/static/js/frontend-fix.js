/**
 * Frontend Fix Manager - Resolves common JavaScript and WebSocket issues
 * This script addresses the h1-check.js error and other frontend issues
 */

(function() {
    'use strict';
    
    console.log('Frontend Fix Manager initializing...');
    
    // 1. Fix for h1-check.js phantom error
    // Create a dummy h1-check object to prevent undefined errors
    if (typeof window.h1Check === 'undefined') {
        window.h1Check = {
            detectStore: function() {
                // Return a dummy store object to prevent errors
                return {
                    getState: () => ({}),
                    dispatch: () => {},
                    subscribe: () => {}
                };
            }
        };
        console.log('h1-check compatibility layer created');
    }
    
    // 2. Enhanced WebSocket connection manager
    class WebSocketManager {
        constructor() {
            this.statusElement = null;
            this.init();
        }
        
        init() {
            // Create status indicator
            this.createStatusIndicator();
            
            // Initialize WebSocket when DOM is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.initializeWebSocket());
            } else {
                this.initializeWebSocket();
            }
        }
        
        createStatusIndicator() {
            this.statusElement = document.createElement('div');
            this.statusElement.className = 'websocket-status connecting';
            this.statusElement.innerHTML = '<i class="bi bi-wifi"></i> Conectando...';
            document.body.appendChild(this.statusElement);
        }
        
        updateStatus(status, message) {
            if (this.statusElement) {
                this.statusElement.className = `websocket-status ${status}`;
                this.statusElement.innerHTML = message;
                
                // Auto-hide success status after 3 seconds
                if (status === 'connected') {
                    setTimeout(() => {
                        if (this.statusElement) {
                            this.statusElement.style.display = 'none';
                        }
                    }, 3000);
                }
            }
        }
        
        initializeWebSocket() {
            // Check if SincronizacionWebSocket is available
            if (typeof SincronizacionWebSocket !== 'undefined') {
                console.log('Initializing WebSocket connection...');
                
                const wsManager = new SincronizacionWebSocket({
                    reconnectInterval: 5000,
                    maxReconnectAttempts: 10
                });
                
                // Add connection callbacks
                wsManager.onConnect((event) => {
                    console.log('WebSocket connected successfully');
                    this.updateStatus('connected', '<i class="bi bi-wifi"></i> Conectado');
                });
                
                wsManager.onDisconnect((event) => {
                    console.log('WebSocket disconnected');
                    this.updateStatus('disconnected', '<i class="bi bi-wifi-off"></i> Desconectado');
                });
                
                // Connect
                wsManager.connect();
                
                // Store globally for access
                window.wsManager = wsManager;
            } else {
                console.warn('SincronizacionWebSocket not available, creating fallback...');
                this.updateStatus('error', '<i class="bi bi-exclamation-triangle"></i> Sin WebSocket');
            }
        }
    }
    
    // 3. FOUC (Flash of Unstyled Content) prevention
    function preventFOUC() {
        // Add loaded class to body when everything is ready
        function markAsLoaded() {
            document.body.classList.add('loaded');
            console.log('Page fully loaded, FOUC prevention complete');
        }
        
        // Wait for fonts and styles to load
        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(markAsLoaded);
        } else {
            // Fallback for browsers without font loading API
            setTimeout(markAsLoaded, 100);
        }
    }
    
    // 4. Error interceptor for missing source maps
    const originalConsoleError = console.error;
    console.error = function(...args) {
        const message = args.join(' ');
        
        // Suppress source map errors that don't affect functionality
        if (message.includes('DevTools failed to load SourceMap') || 
            message.includes('Could not load content for')) {
            // Log to debug but don't spam console
            console.debug('Suppressed source map error:', message);
            return;
        }
        
        // Allow other errors through
        originalConsoleError.apply(console, args);
    };
    
    // 5. Script loading error handler
    function handleScriptErrors() {
        window.addEventListener('error', function(e) {
            // Handle h1-check.js specific errors
            if (e.filename && e.filename.includes('h1-check')) {
                console.warn('h1-check.js error intercepted and handled:', e.message);
                e.preventDefault(); // Prevent error from bubbling up
                return false;
            }
            
            // Handle CDN loading failures
            if (e.target && e.target.tagName === 'SCRIPT') {
                console.error('Script loading failed:', e.target.src);
                
                // Try to provide fallbacks for critical scripts
                if (e.target.src.includes('bootstrap')) {
                    console.warn('Bootstrap CDN failed, functionality may be limited');
                }
                if (e.target.src.includes('alpinejs')) {
                    console.warn('AlpineJS CDN failed, some interactions may not work');
                }
            }
        }, true);
    }
    
    // Initialize all fixes
    function initialize() {
        console.log('Applying frontend fixes...');
        
        // Initialize WebSocket manager
        new WebSocketManager();
        
        // Prevent FOUC
        preventFOUC();
        
        // Handle script errors
        handleScriptErrors();
        
        console.log('Frontend fixes applied successfully');
    }
    
    // Start initialization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
})();
