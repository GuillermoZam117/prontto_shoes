/**
 * Enhanced POS JavaScript - Grid Layout and Advanced Features
 * Sistema POS Pronto Shoes - Enhanced Version
 */

// Enhanced global variables
let currentFilters = {
    marca: '',
    color: '',
    stock: '',
    precioMin: '',
    precioMax: ''
};

let allProducts = []; // Store all products for filtering
let filteredProducts = []; // Store filtered results
let isFiltersVisible = false;

// Enhanced initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize base POS functionality
    if (typeof initializeCarrito === 'function') {
        initializeCarrito();
    }
    
    // Initialize enhanced features
    initializeEnhancedGrid();
    initializeAdvancedFilters();
    initializeQuickActions();
    initializeKeyboardShortcuts();
    loadProductData();
});

/**
 * Initialize enhanced grid functionality
 */
function initializeEnhancedGrid() {
    // Row click handler for product selection
    document.addEventListener('click', function(e) {
        const productRow = e.target.closest('.product-item');
        if (productRow && !e.target.closest('.add-to-cart')) {
            selectProduct(productRow);
        }
    });

    // Enhanced add to cart functionality
    document.addEventListener('click', function(e) {
        if (e.target.closest('.add-to-cart')) {
            e.preventDefault();
            e.stopPropagation();
            
            const productRow = e.target.closest('.product-item');
            const button = e.target.closest('.add-to-cart');
            
            if (productRow && !button.disabled) {
                addToCartFromGrid(productRow);
            }
        }
    });
}

/**
 * Initialize advanced filters
 */
function initializeAdvancedFilters() {
    // Toggle filters visibility
    const toggleFiltersBtn = document.getElementById('toggle-filters');
    if (toggleFiltersBtn) {
        toggleFiltersBtn.addEventListener('click', toggleAdvancedFilters);
    }

    // Filter controls
    const applyFiltersBtn = document.getElementById('apply-filters');
    const clearFiltersBtn = document.getElementById('clear-filters');
    
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', applyAdvancedFilters);
    }
    
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAdvancedFilters);
    }

    // Real-time search enhancement
    const searchInput = document.getElementById('search-products');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleEnhancedSearch, 300));
    }

    // Store selector change
    const tiendaSelect = document.getElementById('tienda-select');
    if (tiendaSelect) {
        tiendaSelect.addEventListener('change', handleStoreChange);
    }
}

/**
 * Initialize quick actions and keyboard shortcuts
 */
function initializeQuickActions() {
    // Double-click to add to cart
    document.addEventListener('dblclick', function(e) {
        const productRow = e.target.closest('.product-item');
        if (productRow) {
            addToCartFromGrid(productRow);
        }
    });
}

/**
 * Initialize enhanced keyboard shortcuts
 */
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Don't process if user is typing in an input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
            return;
        }

        switch(e.key) {
            case 'F1':
                e.preventDefault();
                focusSearch();
                break;
            case 'F2':
                e.preventDefault();
                toggleAdvancedFilters();
                break;
            case 'F3':
                e.preventDefault();
                clearAdvancedFilters();
                break;
            case 'F4':
                e.preventDefault();
                focusCustomerSelect();
                break;
            case 'F5':
                e.preventDefault();
                if (carrito.length > 0) {
                    document.getElementById('checkout-btn')?.click();
                }
                break;
            case 'Escape':
                e.preventDefault();
                clearSelection();
                break;
        }
    });
}

/**
 * Load and prepare product data
 */
function loadProductData() {
    const productRows = document.querySelectorAll('.product-item');
    allProducts = Array.from(productRows).map(row => ({
        element: row,
        codigo: row.dataset.codigo,
        nombre: row.dataset.name,
        marca: row.dataset.brand,
        modelo: row.dataset.model,
        color: row.dataset.color,
        precio: parseFloat(row.dataset.price),
        stock: parseInt(row.dataset.stock),
        storeId: row.dataset.store
    }));

    populateFilterOptions();
    filteredProducts = [...allProducts];
}

/**
 * Populate filter dropdown options
 */
function populateFilterOptions() {
    const marcas = [...new Set(allProducts.map(p => p.marca))].filter(Boolean);
    const colores = [...new Set(allProducts.map(p => p.color))].filter(Boolean);

    populateSelect('filter-marca', marcas);
    populateSelect('filter-color', colores);
}

/**
 * Populate a select element with options
 */
function populateSelect(selectId, options) {
    const select = document.getElementById(selectId);
    if (!select) return;

    // Clear existing options except the first one
    while (select.children.length > 1) {
        select.removeChild(select.lastChild);
    }

    options.sort().forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = option;
        select.appendChild(optionElement);
    });
}

/**
 * Toggle advanced filters visibility
 */
function toggleAdvancedFilters() {
    const filtersDiv = document.getElementById('advanced-filters');
    if (!filtersDiv) return;

    isFiltersVisible = !isFiltersVisible;
    filtersDiv.style.display = isFiltersVisible ? 'block' : 'none';
    
    const toggleBtn = document.getElementById('toggle-filters');
    if (toggleBtn) {
        toggleBtn.innerHTML = isFiltersVisible ? 
            '<i class="bi bi-funnel-fill"></i>' : 
            '<i class="bi bi-funnel"></i>';
    }
}

/**
 * Apply advanced filters
 */
function applyAdvancedFilters() {
    // Get filter values
    currentFilters = {
        marca: document.getElementById('filter-marca')?.value || '',
        color: document.getElementById('filter-color')?.value || '',
        stock: document.getElementById('filter-stock')?.value || '',
        precioMin: parseFloat(document.getElementById('filter-precio-min')?.value) || 0,
        precioMax: parseFloat(document.getElementById('filter-precio-max')?.value) || Infinity
    };

    filterAndDisplayProducts();
}

/**
 * Clear advanced filters
 */
function clearAdvancedFilters() {
    // Reset filter form
    document.getElementById('filter-marca').value = '';
    document.getElementById('filter-color').value = '';
    document.getElementById('filter-stock').value = '';
    document.getElementById('filter-precio-min').value = '';
    document.getElementById('filter-precio-max').value = '';

    // Reset current filters
    currentFilters = {
        marca: '',
        color: '',
        stock: '',
        precioMin: 0,
        precioMax: Infinity
    };

    filterAndDisplayProducts();
}

/**
 * Enhanced search functionality
 */
function handleEnhancedSearch(e) {
    const query = e.target.value.toLowerCase().trim();
    
    // Filter products based on search query
    filteredProducts = allProducts.filter(product => {
        const searchableText = [
            product.codigo,
            product.nombre,
            product.marca,
            product.modelo,
            product.color
        ].join(' ').toLowerCase();
        
        return query === '' || searchableText.includes(query);
    });

    filterAndDisplayProducts();
}

/**
 * Handle store selection change
 */
function handleStoreChange(e) {
    const selectedStoreId = e.target.value;
    
    // Show/hide products based on store selection
    allProducts.forEach(product => {
        if (selectedStoreId === '' || product.storeId === selectedStoreId) {
            product.element.style.display = '';
        } else {
            product.element.style.display = 'none';
        }
    });

    // Update filter options for current store
    const storeProducts = allProducts.filter(p => 
        selectedStoreId === '' || p.storeId === selectedStoreId
    );
    
    const marcas = [...new Set(storeProducts.map(p => p.marca))].filter(Boolean);
    const colores = [...new Set(storeProducts.map(p => p.color))].filter(Boolean);
    
    populateSelect('filter-marca', marcas);
    populateSelect('filter-color', colores);
}

/**
 * Filter and display products based on current criteria
 */
function filterAndDisplayProducts() {
    let visibleCount = 0;
    
    filteredProducts.forEach(product => {
        let shouldShow = true;
        
        // Apply filters
        if (currentFilters.marca && product.marca !== currentFilters.marca) {
            shouldShow = false;
        }
        
        if (currentFilters.color && product.color !== currentFilters.color) {
            shouldShow = false;
        }
        
        if (currentFilters.stock) {
            switch (currentFilters.stock) {
                case 'disponible':
                    shouldShow = shouldShow && product.stock > 0;
                    break;
                case 'bajo':
                    shouldShow = shouldShow && product.stock <= 10 && product.stock > 0;
                    break;
                case 'agotado':
                    shouldShow = shouldShow && product.stock === 0;
                    break;
            }
        }
        
        if (product.precio < currentFilters.precioMin || product.precio > currentFilters.precioMax) {
            shouldShow = false;
        }

        // Show/hide product row
        if (shouldShow) {
            product.element.style.display = '';
            visibleCount++;
        } else {
            product.element.style.display = 'none';
        }
    });

    // Update results count (you can add a counter display)
    updateResultsCount(visibleCount);
}

/**
 * Update results count display
 */
function updateResultsCount(count) {
    // You can implement a results counter here
    console.log(`Showing ${count} products`);
}

/**
 * Select a product row
 */
function selectProduct(productRow) {
    // Clear previous selection
    document.querySelectorAll('.product-item.selected').forEach(row => {
        row.classList.remove('selected');
    });

    // Select current row
    productRow.classList.add('selected');
    productoSeleccionado = {
        id: productRow.dataset.productId,
        codigo: productRow.dataset.codigo,
        nombre: productRow.dataset.name,
        precio: parseFloat(productRow.dataset.price),
        stock: parseInt(productRow.dataset.stock)
    };
}

/**
 * Clear current selection
 */
function clearSelection() {
    document.querySelectorAll('.product-item.selected').forEach(row => {
        row.classList.remove('selected');
    });
    productoSeleccionado = null;
}

/**
 * Add product to cart from grid
 */
function addToCartFromGrid(productRow) {
    const productData = {
        id: productRow.dataset.productId,
        codigo: productRow.dataset.codigo,
        nombre: productRow.dataset.name,
        marca: productRow.dataset.brand,
        modelo: productRow.dataset.model,
        color: productRow.dataset.color,
        precio: parseFloat(productRow.dataset.price),
        stock: parseInt(productRow.dataset.stock)
    };

    // Check if product is already in cart
    const existingItem = carrito.find(item => item.id === productData.id);
    
    if (existingItem) {
        if (existingItem.cantidad < productData.stock) {
            existingItem.cantidad++;
            showNotification('Cantidad actualizada', 'success');
        } else {
            showNotification('Stock insuficiente', 'warning');
        }
    } else {
        if (productData.stock > 0) {
            carrito.push({
                id: productData.id,
                codigo: productData.codigo,
                nombre: productData.nombre,
                precio: productData.precio,
                cantidad: 1,
                stock: productData.stock
            });
            showNotification('Producto agregado al carrito', 'success');
        } else {
            showNotification('Producto sin stock', 'error');
        }
    }

    // Update cart display and save to localStorage
    if (typeof actualizarVista === 'function') {
        actualizarVista();
    }
    
    // Add visual feedback
    addVisualFeedback(productRow);
}

/**
 * Add visual feedback when adding to cart
 */
function addVisualFeedback(productRow) {
    const addButton = productRow.querySelector('.add-to-cart');
    if (addButton) {
        const originalHTML = addButton.innerHTML;
        addButton.innerHTML = '<i class="bi bi-check"></i>';
        addButton.classList.add('btn-success');
        
        setTimeout(() => {
            addButton.innerHTML = originalHTML;
            addButton.classList.remove('btn-success');
        }, 1000);
    }
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    // Use ProntoApp.notify if available, otherwise console log
    if (typeof ProntoApp !== 'undefined' && ProntoApp.notify) {
        ProntoApp.notify('POS', message, type);
    } else {
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

/**
 * Focus search input
 */
function focusSearch() {
    const searchInput = document.getElementById('search-products');
    if (searchInput) {
        searchInput.focus();
        searchInput.select();
    }
}

/**
 * Focus customer select
 */
function focusCustomerSelect() {
    const customerSelect = document.getElementById('cliente-select');
    if (customerSelect) {
        customerSelect.focus();
    }
}

/**
 * Debounce function for search optimization
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Enhanced cart operations (if not already implemented)
 */
function updateCartQuantity(productId, newQuantity) {
    const item = carrito.find(item => item.id === productId);
    if (item) {
        if (newQuantity <= 0) {
            removeFromCart(productId);
        } else if (newQuantity <= item.stock) {
            item.cantidad = newQuantity;
            if (typeof actualizarVista === 'function') {
                actualizarVista();
            }
        } else {
            showNotification('Cantidad excede el stock disponible', 'warning');
        }
    }
}

function removeFromCart(productId) {
    const index = carrito.findIndex(item => item.id === productId);
    if (index > -1) {
        carrito.splice(index, 1);
        if (typeof actualizarVista === 'function') {
            actualizarVista();
        }
        showNotification('Producto removido del carrito', 'info');
    }
}

// Export functions for global access if needed
window.PosEnhanced = {
    selectProduct,
    clearSelection,
    addToCartFromGrid,
    updateCartQuantity,
    removeFromCart,
    applyAdvancedFilters,
    clearAdvancedFilters,
    toggleAdvancedFilters
};
