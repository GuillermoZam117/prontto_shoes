/**
 * Sidebar Management System - FIXED VERSION
 * Handles sidebar toggle, state persistence, and dropdown functionality
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
        this.isMobile = false;
        this.isCollapsed = false;
        
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
        this.checkMobileView();
        this.updateLayout();
        
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
        
        this.isCollapsed = this.config.collapsed;
    }
    
    /**
     * Save sidebar state to localStorage
     */
    saveState() {
        try {
            const state = {
                collapsed: this.isCollapsed,
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
                this.updateBranding();
                console.log('✓ Business configuration loaded');
            } else {
                console.warn('Failed to load business configuration');
                this.setDefaultBranding();
            }
        } catch (error) {
            console.warn('Error loading business configuration:', error);
            this.setDefaultBranding();
        }
    }
    
    /**
     * Update branding based on business config
     */
    updateBranding() {
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
        
        // Apply custom colors if available
        if (config.color_primario) {
            document.documentElement.style.setProperty('--sidebar-active', config.color_primario);
        }

        // Update page title if needed
        if (config.nombre_negocio) {
            const currentTitle = document.title;
            if (!currentTitle.includes(config.nombre_negocio)) {
                document.title = `${config.nombre_negocio} | Sistema POS`;
            }
        }
    }
    
    /**
     * Set default branding
     */
    setDefaultBranding() {
        const brandText = document.getElementById('sidebarBrand');
        if (brandText && !brandText.textContent.trim()) {
            brandText.textContent = 'POS System';
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
            this.mobileMenuBtn.addEventListener('click', () => this.toggleMobileSidebar());
        }
        
        // Mobile overlay
        if (this.sidebarOverlay) {
            this.sidebarOverlay.addEventListener('click', () => this.closeMobileSidebar());
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
        
        // Window resize
        window.addEventListener('resize', () => {
            this.checkMobileView();
            this.updateLayout();
        });
    }
    
    /**
     * Initialize dropdown functionality - FIXED VERSION
     */
    initializeDropdowns() {
        const dropdownToggles = document.querySelectorAll('.nav-dropdown-toggle');
        
        console.log(`🔧 Initializing ${dropdownToggles.length} dropdown toggles...`);
        
        dropdownToggles.forEach((toggle, index) => {
            const dropdownName = toggle.querySelector('.nav-text')?.textContent || `Dropdown ${index + 1}`;
            console.log(`🔧 Setting up dropdown: ${dropdownName}`);
            
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                console.log(`🖱️ Dropdown clicked: ${dropdownName}`);
                
                const dropdown = toggle.closest('.nav-dropdown');
                if (!dropdown) {
                    console.error('❌ No dropdown container found!');
                    return;
                }
                
                const isOpen = dropdown.classList.contains('open');
                console.log(`📊 Dropdown "${dropdownName}" is currently: ${isOpen ? 'OPEN' : 'CLOSED'}`);
                
                // Close all other dropdowns
                document.querySelectorAll('.nav-dropdown.open').forEach(openDropdown => {
                    if (openDropdown !== dropdown) {
                        openDropdown.classList.remove('open');
                        console.log('🔽 Closing other dropdown');
                    }
                });
                
                // Toggle current dropdown
                dropdown.classList.toggle('open', !isOpen);
                console.log(`${!isOpen ? '🔼' : '🔽'} ${!isOpen ? 'Opening' : 'Closing'} dropdown: ${dropdownName}`);
            });
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.nav-dropdown')) {
                const openDropdowns = document.querySelectorAll('.nav-dropdown.open');
                if (openDropdowns.length > 0) {
                    console.log('🔽 Closing all dropdowns (clicked outside)');
                    openDropdowns.forEach(dropdown => {
                        dropdown.classList.remove('open');
                    });
                }
            }
        });
        
        console.log('✅ Dropdown initialization complete');
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
            this.closeMobileSidebar();
        }
    }
    
    /**
     * Check if mobile view
     */
    checkMobileView() {
        this.isMobile = window.innerWidth <= 768;
    }
    
    /**
     * Toggle sidebar
     */
    toggleSidebar() {
        if (this.isMobile) {
            this.toggleMobileSidebar();
        } else {
            this.isCollapsed = !this.isCollapsed;
            this.updateLayout();
            this.saveState();
        }
    }
    
    /**
     * Toggle mobile sidebar
     */
    toggleMobileSidebar() {
        const isOpen = this.sidebar?.classList.contains('show');
        if (isOpen) {
            this.closeMobileSidebar();
        } else {
            this.openMobileSidebar();
        }
    }
    
    /**
     * Open mobile sidebar
     */
    openMobileSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.add('show');
        }
        if (this.sidebarOverlay) {
            this.sidebarOverlay.classList.add('show');
        }
        document.body.style.overflow = 'hidden';
    }
    
    /**
     * Close mobile sidebar
     */
    closeMobileSidebar() {
        if (this.sidebar) {
            this.sidebar.classList.remove('show');
        }
        if (this.sidebarOverlay) {
            this.sidebarOverlay.classList.remove('show');
        }
        document.body.style.overflow = '';
    }
    
    /**
     * Update layout based on current state
     */
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
    
    /**
     * Public methods for external use
     */
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
        window.sidebarManager = sidebarManager;
    });
} else {
    sidebarManager = new SidebarManager();
    window.sidebarManager = sidebarManager;
}

// Global keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + B to toggle sidebar
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        if (window.sidebarManager) {
            window.sidebarManager.toggleSidebar();
        }
    }
});

console.log('🚀 Sidebar JavaScript loaded successfully');
