/**
 * Sidebar Management System
 * Handles sidebar toggle, state persistence, and business configuration loading
 */
class SidebarManager {
    constructor() {
        this.sidebar = null;
        this.mainContent = null;
        this.sidebarToggle = null;
        this.mobileMenuBtn = null;
        this.sidebarOverlay = null;
        this.dropdownToggles = [];
        
        this.config = {
            collapsed: false,
            theme: 'dark',
            businessConfig: null
        };
        
        this.storageKey = 'pos_sidebar_state';
        this.apiEndpoint = '/api/configuracion/publica/';
        
        this.init();
    }
    
    /**
     * Initialize the sidebar manager
     */
    init() {
        this.bindElements();
        this.loadStoredState();
        this.loadBusinessConfig();
        this.bindEvents();
        this.initializeDropdowns();
        this.handleResponsive();
        
        console.log('✓ Sidebar Manager initialized');
    }
    
    /**
     * Bind DOM elements
     */
    bindElements() {
        this.sidebar = document.getElementById('posSidebar');
        this.mainContent = document.getElementById('mainContent');
        this.sidebarToggle = document.getElementById('sidebarToggle');
        this.mobileMenuBtn = document.getElementById('mobileMenuBtn');
        this.sidebarOverlay = document.getElementById('sidebarOverlay');
        this.dropdownToggles = document.querySelectorAll('.nav-dropdown-toggle');
    }
    
    /**
     * Load stored sidebar state from localStorage
     */
    loadStoredState() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                const state = JSON.parse(stored);
                this.config.collapsed = state.collapsed || false;
            } else {
                // Use default from body data attribute
                const bodyCollapsed = document.body.getAttribute('data-sidebar-collapsed');
                this.config.collapsed = bodyCollapsed === 'true';
            }
        } catch (error) {
            console.warn('Error loading sidebar state:', error);
            this.config.collapsed = false;
        }
        
        this.applySidebarState();
    }
    
    /**
     * Save sidebar state to localStorage
     */
    saveState() {
        try {
            const state = {
                collapsed: this.config.collapsed,
                timestamp: Date.now()
            };
            localStorage.setItem(this.storageKey, JSON.stringify(state));
        } catch (error) {
            console.warn('Error saving sidebar state:', error);
        }
    }
    
    /**
     * Load business configuration from API
     */
    async loadBusinessConfig() {
        try {
            const response = await fetch(this.apiEndpoint, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (response.ok) {
                this.config.businessConfig = await response.json();
                this.applyBusinessConfig();
                console.log('✓ Business configuration loaded');
            } else {
                console.warn('Failed to load business configuration');
            }
        } catch (error) {
            console.error('Error loading business configuration:', error);
        }
    }
    
    /**
     * Apply business configuration to sidebar
     */
    applyBusinessConfig() {
        if (!this.config.businessConfig) return;
        
        const config = this.config.businessConfig;
        
        // Update logo and brand text
        const logoImg = document.getElementById('sidebarLogoImg');
        const brandText = document.getElementById('sidebarBrand');
        
        if (logoImg && config.logo_url) {
            logoImg.src = config.logo_url;
            logoImg.alt = config.nombre_negocio;
        }
        
        if (brandText) {
            brandText.textContent = config.logo_texto || config.nombre_negocio;
        }
        
        // Apply theme
        if (config.sidebar_theme) {
            this.config.theme = config.sidebar_theme;
            this.applyTheme();
        }
        
        // Apply custom colors if available
        if (config.color_primario) {
            document.documentElement.style.setProperty('--sidebar-active', config.color_primario);
        }
        
        // Update page title if needed
        const currentTitle = document.title;
        if (!currentTitle.includes(config.nombre_negocio)) {
            document.title = currentTitle.replace('POS System', config.nombre_negocio);
        }
    }
    
    /**
     * Apply theme to sidebar
     */
    applyTheme() {
        if (!this.sidebar) return;
        
        // Remove existing theme classes
        this.sidebar.classList.remove('theme-light', 'theme-dark', 'theme-primary');
        
        // Add current theme class
        this.sidebar.classList.add(`theme-${this.config.theme}`);
    }
    
    /**
     * Apply sidebar collapsed/expanded state
     */
    applySidebarState() {
        if (!this.sidebar || !this.mainContent) return;
        
        if (this.config.collapsed) {
            this.sidebar.classList.add('collapsed');
            this.mainContent.classList.add('sidebar-collapsed');
        } else {
            this.sidebar.classList.remove('collapsed');
            this.mainContent.classList.remove('sidebar-collapsed');
        }
    }
    
    /**
     * Bind event listeners
     */
    bindEvents() {
        // Desktop sidebar toggle
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }
        
        // Mobile menu button
        if (this.mobileMenuBtn) {
            this.mobileMenuBtn.addEventListener('click', () => this.showMobileSidebar());
        }
        
        // Mobile overlay
        if (this.sidebarOverlay) {
            this.sidebarOverlay.addEventListener('click', () => this.hideMobileSidebar());
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Window resize
        window.addEventListener('resize', () => this.handleResize());
        
        // Page visibility change (to refresh config when returning to tab)
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.loadBusinessConfig();
            }
        });
    }
    
    /**
     * Initialize dropdown functionality
     */
    initializeDropdowns() {
        this.dropdownToggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleDropdown(toggle.closest('.nav-dropdown'));
            });
        });
    }
    
    /**
     * Toggle dropdown menu
     */
    toggleDropdown(dropdown) {
        if (!dropdown) return;
        
        const isOpen = dropdown.classList.contains('open');
        
        // Close all other dropdowns
        this.dropdownToggles.forEach(toggle => {
            toggle.closest('.nav-dropdown').classList.remove('open');
        });
        
        // Toggle current dropdown
        if (!isOpen) {
            dropdown.classList.add('open');
        }
    }
    
    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(e) {
        // Ctrl+B or Cmd+B to toggle sidebar
        if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
            e.preventDefault();
            this.toggleSidebar();
        }
        
        // ESC to close mobile sidebar
        if (e.key === 'Escape') {
            this.hideMobileSidebar();
        }
    }
    
    /**
     * Handle window resize
     */
    handleResize() {
        // Close mobile sidebar on larger screens
        if (window.innerWidth >= 768) {
            this.hideMobileSidebar();
        }
    }
    
    /**
     * Handle responsive behavior
     */
    handleResponsive() {
        if (window.innerWidth < 768) {
            // On mobile, always start with sidebar hidden
            this.hideMobileSidebar();
        }
    }
    
    /**
     * Toggle sidebar (desktop)
     */
    toggleSidebar() {
        if (window.innerWidth < 768) {
            this.toggleMobileSidebar();
        } else {
            this.config.collapsed = !this.config.collapsed;
            this.applySidebarState();
            this.saveState();
        }
    }
    
    /**
     * Expand sidebar
     */
    expand() {
        if (window.innerWidth < 768) {
            this.showMobileSidebar();
        } else {
            this.config.collapsed = false;
            this.applySidebarState();
            this.saveState();
        }
    }
    
    /**
     * Collapse sidebar
     */
    collapse() {
        if (window.innerWidth < 768) {
            this.hideMobileSidebar();
        } else {
            this.config.collapsed = true;
            this.applySidebarState();
            this.saveState();
        }
    }
    
    /**
     * Show mobile sidebar
     */
    showMobileSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.add('show');
        }
        if (this.sidebarOverlay) {
            this.sidebarOverlay.classList.add('show');
        }
        document.body.classList.add('sidebar-open');
    }
    
    /**
     * Hide mobile sidebar
     */
    hideMobileSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.remove('show');
        }
        if (this.sidebarOverlay) {
            this.sidebarOverlay.classList.remove('show');
        }
        document.body.classList.remove('sidebar-open');
    }
    
    /**
     * Toggle mobile sidebar
     */
    toggleMobileSidebar() {
        if (this.sidebar && this.sidebar.classList.contains('show')) {
            this.hideMobileSidebar();
        } else {
            this.showMobileSidebar();
        }
    }
    
    /**
     * Refresh configuration from server
     */
    async refresh() {
        await this.loadBusinessConfig();
        console.log('✓ Sidebar configuration refreshed');
    }
    
    /**
     * Get current sidebar state
     */
    isCurrentlyCollapsed() {
        if (window.innerWidth < 768) {
            return !this.sidebar?.classList.contains('show');
        }
        return this.config.collapsed;
    }
    
    /**
     * Get business configuration
     */
    getBusinessConfig() {
        return this.config.businessConfig;
    }
    
    /**
     * Update business configuration (for admin changes)
     */
    updateBusinessConfig(newConfig) {
        this.config.businessConfig = { ...this.config.businessConfig, ...newConfig };
        this.applyBusinessConfig();
    }
}

// Initialize sidebar manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar manager
    window.sidebarManager = new SidebarManager();
    
    // Make it globally available for debugging
    if (window.console && window.console.log) {
        console.log('✓ Sidebar Manager available globally as window.sidebarManager');
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SidebarManager;
}
            this.mobileMenuBtn.addEventListener('click', () => {
                this.toggleMobileSidebar();
            });
        }

        // Close mobile sidebar when clicking overlay
        if (this.sidebarOverlay) {
            this.sidebarOverlay.addEventListener('click', () => {
                this.closeMobileSidebar();
            });
        }

        // Window resize handler
        window.addEventListener('resize', () => {
            this.checkMobileView();
            this.updateLayout();
        });

        // ESC key to close mobile sidebar
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isMobile) {
                this.closeMobileSidebar();
            }
        });
    }

    async loadBusinessConfig() {
        try {
            const response = await fetch('/api/configuracion/publica/');
            if (response.ok) {
                this.businessConfig = await response.json();
                this.updateBranding();
            }
        } catch (error) {
            console.warn('Could not load business configuration:', error);
            this.setDefaultBranding();
        }
    }

    updateBranding() {
        if (!this.businessConfig) return;

        // Update logo
        const logoImg = document.querySelector('.sidebar-logo img');
        const logoText = document.querySelector('.sidebar-brand');

        if (logoImg && this.businessConfig.logo) {
            logoImg.src = this.businessConfig.logo;
            logoImg.alt = this.businessConfig.nombre_negocio || 'Logo';
        }

        if (logoText) {
            logoText.textContent = this.businessConfig.logo_texto || this.businessConfig.nombre_negocio || 'POS System';
        }

        // Update colors if provided
        if (this.businessConfig.color_primario) {
            document.documentElement.style.setProperty('--sidebar-active', this.businessConfig.color_primario);
        }

        // Update page title
        if (this.businessConfig.nombre_negocio) {
            const currentTitle = document.title;
            if (!currentTitle.includes(this.businessConfig.nombre_negocio)) {
                document.title = `${this.businessConfig.nombre_negocio} | Sistema POS`;
            }
        }
    }

    setDefaultBranding() {
        const logoText = document.querySelector('.sidebar-brand');
        if (logoText && !logoText.textContent.trim()) {
            logoText.textContent = 'POS System';
        }
    }

    checkMobileView() {
        this.isMobile = window.innerWidth <= 768;
    }

    toggleSidebar() {
        if (this.isMobile) {
            this.toggleMobileSidebar();
        } else {
            this.toggleDesktopSidebar();
        }
    }

    toggleDesktopSidebar() {
        this.isCollapsed = !this.isCollapsed;
        this.updateLayout();
        this.saveState();
    }

    toggleMobileSidebar() {
        const isOpen = this.sidebar?.classList.contains('show');
        
        if (isOpen) {
            this.closeMobileSidebar();
        } else {
            this.openMobileSidebar();
        }
    }

    openMobileSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.add('show');
        }
        if (this.sidebarOverlay) {
            this.sidebarOverlay.classList.add('show');
        }
        document.body.style.overflow = 'hidden';
    }

    closeMobileSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.remove('show');
        }
        if (this.sidebarOverlay) {
            this.sidebarOverlay.classList.remove('show');
        }
        document.body.style.overflow = '';
    }

    updateLayout() {
        if (!this.sidebar || !this.mainContent) return;

        if (this.isMobile) {
            // Mobile layout
            this.sidebar.classList.remove('collapsed');
            this.mainContent.classList.remove('sidebar-collapsed');
        } else {
            // Desktop layout
            if (this.isCollapsed) {
                this.sidebar.classList.add('collapsed');
                this.mainContent.classList.add('sidebar-collapsed');
            } else {
                this.sidebar.classList.remove('collapsed');
                this.mainContent.classList.remove('sidebar-collapsed');
            }
        }
    }

    setupDropdowns() {
        const dropdownToggles = document.querySelectorAll('.nav-dropdown-toggle');
        
        dropdownToggles.forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                
                const dropdown = toggle.closest('.nav-dropdown');
                const isOpen = dropdown.classList.contains('open');
                
                // Close all other dropdowns
                document.querySelectorAll('.nav-dropdown.open').forEach(openDropdown => {
                    if (openDropdown !== dropdown) {
                        openDropdown.classList.remove('open');
                    }
                });
                
                // Toggle current dropdown
                dropdown.classList.toggle('open', !isOpen);
            });
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.nav-dropdown')) {
                document.querySelectorAll('.nav-dropdown.open').forEach(dropdown => {
                    dropdown.classList.remove('open');
                });
            }
        });
    }

    saveState() {
        if (!this.isMobile) {
            localStorage.setItem('sidebarCollapsed', this.isCollapsed.toString());
        }
    }

    restoreState() {
        if (!this.isMobile) {
            const savedState = localStorage.getItem('sidebarCollapsed');
            if (savedState !== null) {
                this.isCollapsed = savedState === 'true';
            } else if (this.businessConfig?.sidebar_collapsed_default) {
                this.isCollapsed = this.businessConfig.sidebar_collapsed_default;
            }
        }
    }

    // Public methods for external use
    collapse() {
        if (!this.isMobile) {
            this.isCollapsed = true;
            this.updateLayout();
            this.saveState();
        }
    }

    expand() {
        if (!this.isMobile) {
            this.isCollapsed = false;
            this.updateLayout();
            this.saveState();
        }
    }

    isCurrentlyCollapsed() {
        return this.isCollapsed && !this.isMobile;
    }

    refresh() {
        this.loadBusinessConfig();
        this.updateLayout();
    }
}

// Initialize sidebar when DOM is ready
let sidebarManager;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        sidebarManager = new SidebarManager();
    });
} else {
    sidebarManager = new SidebarManager();
}

// Export for global access
window.sidebarManager = sidebarManager;

// Optional: Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + B to toggle sidebar
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        if (sidebarManager) {
            sidebarManager.toggleSidebar();
        }
    }
});

// Auto-refresh business config periodically (every 5 minutes)
setInterval(() => {
    if (sidebarManager) {
        sidebarManager.loadBusinessConfig();
    }
}, 5 * 60 * 1000);
