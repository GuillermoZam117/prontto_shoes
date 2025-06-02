/**
 * Sistema POS Pronto Shoes - Pedidos Avanzados
 * JavaScript utilities and functions
 */

// Global configuration
const CONFIG = {
    API_BASE_URL: '/api/pedidos-avanzados/',
    NOTIFICATION_DURATION: 3000,
    AUTO_REFRESH_INTERVAL: 30000,
    CURRENCY_SYMBOL: '$',
    DATE_FORMAT: 'DD/MM/YYYY',
    DATETIME_FORMAT: 'DD/MM/YYYY HH:mm'
};

// Utility Functions
const Utils = {
    /**
     * Format currency values
     */
    formatCurrency: function(amount) {
        return CONFIG.CURRENCY_SYMBOL + parseFloat(amount).toLocaleString('es-AR', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    },

    /**
     * Format dates
     */
    formatDate: function(date, format = CONFIG.DATE_FORMAT) {
        if (!date) return '-';
        const d = new Date(date);
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        
        if (format === CONFIG.DATETIME_FORMAT) {
            return `${day}/${month}/${year} ${hours}:${minutes}`;
        }
        return `${day}/${month}/${year}`;
    },

    /**
     * Debounce function
     */
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Get CSRF token
     */
    getCSRFToken: function() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    },

    /**
     * Generate random ID
     */
    generateId: function() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    },

    /**
     * Validate email
     */
    validateEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    /**
     * Validate phone
     */
    validatePhone: function(phone) {
        const re = /^[\+]?[1-9][\d]{0,15}$/;
        return re.test(phone.replace(/\s/g, ''));
    },

    /**
     * Copy text to clipboard
     */
    copyToClipboard: function(text) {
        if (navigator.clipboard) {
            return navigator.clipboard.writeText(text);
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return Promise.resolve();
        }
    }
};

// Notification System
const Notifications = {
    container: null,

    init: function() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1050;
                max-width: 350px;
            `;
            document.body.appendChild(this.container);
        }
    },

    show: function(message, type = 'info', duration = CONFIG.NOTIFICATION_DURATION) {
        this.init();
        
        const notification = document.createElement('div');
        const id = Utils.generateId();
        
        notification.className = `notification ${type} animate-fade-in`;
        notification.id = id;
        notification.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span>${message}</span>
                <button type="button" class="btn-close btn-close-white ms-2" onclick="Notifications.hide('${id}')"></button>
            </div>
        `;
        
        this.container.appendChild(notification);
        
        // Auto hide
        if (duration > 0) {
            setTimeout(() => this.hide(id), duration);
        }
        
        return id;
    },

    hide: function(id) {
        const notification = document.getElementById(id);
        if (notification) {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }
    },

    success: function(message, duration) {
        return this.show(message, 'success', duration);
    },

    error: function(message, duration) {
        return this.show(message, 'error', duration);
    },

    warning: function(message, duration) {
        return this.show(message, 'warning', duration);
    },

    info: function(message, duration) {
        return this.show(message, 'info', duration);
    }
};

// API Client
const API = {
    /**
     * Make API request
     */
    request: async function(endpoint, options = {}) {
        const url = CONFIG.API_BASE_URL + endpoint;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': Utils.getCSRFToken()
            }
        };
        
        const config = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    /**
     * GET request
     */
    get: function(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    /**
     * POST request
     */
    post: function(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    /**
     * PUT request
     */
    put: function(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    /**
     * PATCH request
     */
    patch: function(endpoint, data) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    },

    /**
     * DELETE request
     */
    delete: function(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
};

// Loading Manager
const Loading = {
    overlay: null,

    init: function() {
        if (!this.overlay) {
            this.overlay = document.createElement('div');
            this.overlay.className = 'loading-overlay';
            this.overlay.style.display = 'none';
            this.overlay.innerHTML = `
                <div class="text-center">
                    <div class="spinner"></div>
                    <p class="mt-3 text-white">Cargando...</p>
                </div>
            `;
            document.body.appendChild(this.overlay);
        }
    },

    show: function(message = 'Cargando...') {
        this.init();
        this.overlay.querySelector('p').textContent = message;
        this.overlay.style.display = 'flex';
    },

    hide: function() {
        if (this.overlay) {
            this.overlay.style.display = 'none';
        }
    }
};

// Modal Manager
const Modal = {
    /**
     * Show confirmation modal
     */
    confirm: function(message, title = 'Confirmar') {
        return new Promise((resolve) => {
            const modalHtml = `
                <div class="modal fade" id="confirmModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">${title}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <p>${message}</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" onclick="Modal.resolveConfirm(false)">Cancelar</button>
                                <button type="button" class="btn btn-primary" onclick="Modal.resolveConfirm(true)">Confirmar</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal
            const existingModal = document.getElementById('confirmModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // Add new modal
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            // Store resolve function
            this._confirmResolve = resolve;
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
            modal.show();
        });
    },

    resolveConfirm: function(result) {
        if (this._confirmResolve) {
            this._confirmResolve(result);
            this._confirmResolve = null;
        }
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));
        if (modal) {
            modal.hide();
        }
    }
};

// Form Validation
const Validation = {
    /**
     * Validate form
     */
    validateForm: function(formElement) {
        const errors = [];
        const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                errors.push(`El campo ${this.getFieldLabel(input)} es requerido`);
                this.markFieldError(input);
            } else {
                this.clearFieldError(input);
            }
            
            // Specific validations
            if (input.type === 'email' && input.value && !Utils.validateEmail(input.value)) {
                errors.push(`El email ${input.value} no es válido`);
                this.markFieldError(input);
            }
            
            if (input.type === 'tel' && input.value && !Utils.validatePhone(input.value)) {
                errors.push(`El teléfono ${input.value} no es válido`);
                this.markFieldError(input);
            }
        });
        
        return errors;
    },

    getFieldLabel: function(input) {
        const label = input.previousElementSibling;
        if (label && label.tagName === 'LABEL') {
            return label.textContent.replace('*', '').trim();
        }
        return input.name || input.id || 'campo';
    },

    markFieldError: function(input) {
        input.classList.add('is-invalid');
    },

    clearFieldError: function(input) {
        input.classList.remove('is-invalid');
    }
};

// Auto-refresh Manager
const AutoRefresh = {
    intervals: new Map(),

    start: function(key, callback, interval = CONFIG.AUTO_REFRESH_INTERVAL) {
        this.stop(key); // Stop existing interval
        
        const intervalId = setInterval(() => {
            if (document.visibilityState === 'visible') {
                callback();
            }
        }, interval);
        
        this.intervals.set(key, intervalId);
    },

    stop: function(key) {
        const intervalId = this.intervals.get(key);
        if (intervalId) {
            clearInterval(intervalId);
            this.intervals.delete(key);
        }
    },

    stopAll: function() {
        this.intervals.forEach((intervalId) => {
            clearInterval(intervalId);
        });
        this.intervals.clear();
    }
};

// Local Storage Manager
const Storage = {
    /**
     * Set item in localStorage
     */
    set: function(key, value) {
        try {
            localStorage.setItem(`pos_${key}`, JSON.stringify(value));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    },

    /**
     * Get item from localStorage
     */
    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(`pos_${key}`);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return defaultValue;
        }
    },

    /**
     * Remove item from localStorage
     */
    remove: function(key) {
        try {
            localStorage.removeItem(`pos_${key}`);
        } catch (error) {
            console.error('Error removing from localStorage:', error);
        }
    },

    /**
     * Clear all localStorage
     */
    clear: function() {
        try {
            Object.keys(localStorage).forEach(key => {
                if (key.startsWith('pos_')) {
                    localStorage.removeItem(key);
                }
            });
        } catch (error) {
            console.error('Error clearing localStorage:', error);
        }
    }
};

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    Notifications.init();
    Loading.init();
    
    // Global click handlers
    document.addEventListener('click', function(e) {
        // Handle copy buttons
        if (e.target.matches('[data-copy]')) {
            const text = e.target.getAttribute('data-copy');
            Utils.copyToClipboard(text).then(() => {
                Notifications.success('Copiado al portapapeles');
            });
        }
        
        // Handle external links
        if (e.target.matches('a[href^="http"]')) {
            e.target.setAttribute('target', '_blank');
            e.target.setAttribute('rel', 'noopener noreferrer');
        }
    });
    
    // Handle form submissions
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.classList.contains('validate')) {
            e.preventDefault();
            
            const errors = Validation.validateForm(form);
            if (errors.length > 0) {
                Notifications.error(errors.join('<br>'));
                return;
            }
            
            // Continue with form submission
            form.submit();
        }
    });
    
    // Handle input changes for real-time validation
    document.addEventListener('input', function(e) {
        const input = e.target;
        if (input.matches('input, select, textarea')) {
            Validation.clearFieldError(input);
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('#search, [name="search"], .search-input');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Esc to close modals
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                if (modal) {
                    modal.hide();
                }
            }
        }
    });
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    AutoRefresh.stopAll();
});

// Export global functions for template use
window.showNotification = Notifications.show.bind(Notifications);
window.formatCurrency = Utils.formatCurrency;
window.formatDate = Utils.formatDate;
window.copyToClipboard = Utils.copyToClipboard;
window.confirmAction = Modal.confirm.bind(Modal);

// Export modules for advanced usage
window.POS = {
    Utils,
    Notifications,
    API,
    Loading,
    Modal,
    Validation,
    AutoRefresh,
    Storage,
    CONFIG
};
