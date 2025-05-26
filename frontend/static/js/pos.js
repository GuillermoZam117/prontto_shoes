/**
 * Punto de Venta - JavaScript Client-side Logic
 * Sistema POS Pronto Shoes
 */

// Global variables
let carrito = []; // Array to store cart items
let cliente = null; // Selected customer
let descuentoAplicado = 0; // Applied discount percentage
let subTotal = 0; // Subtotal (before discount)
let totalVenta = 0; // Total (after discount)
let tiendaId = null; // Store ID
let productoSeleccionado = null; // Currently selected product
let timeoutBusqueda = null; // Timeout for search to avoid too many requests
let scannerInput = ''; // Barcode scanner input
let scannerTimeout = null; // Timeout for the barcode scanner

// Initialize the POS system
document.addEventListener('DOMContentLoaded', function() {
    // Set tienda_id from the hidden input
    const tiendaIdInput = document.getElementById('tienda_id');
    if (tiendaIdInput) {
        tiendaId = tiendaIdInput.value;
    }
    
    // Initialize cart from localStorage if exists
    initializeCarrito();
    
    // Initialize search functionality
    initializeSearch();
    
    // Initialize barcode scanner functionality
    initializeBarcodeScanner();
    
    // Initialize customer selection
    initializeClienteSelection();
    
    // Initialize payment processing
    initializePayment();
    
    // Initialize hotkeys
    initializeHotkeys();
    
    // Load categories
    loadCategorias();
});

/**
 * Initialize the shopping cart
 */
function initializeCarrito() {
    try {
        const savedCarrito = localStorage.getItem('pos_carrito');
        const savedCliente = localStorage.getItem('pos_cliente');
        
        if (savedCarrito) {
            carrito = JSON.parse(savedCarrito);
            actualizarVista();
        }
        
        if (savedCliente) {
            cliente = JSON.parse(savedCliente);
            const clienteSelect = document.getElementById('cliente');
            if (clienteSelect && cliente) {
                clienteSelect.value = cliente.id;
                
                // Display customer information
                document.getElementById('cliente_info').innerHTML = `
                    <div class="alert alert-info">
                        <strong>${cliente.nombre}</strong>
                        ${cliente.descuento > 0 ? ` - Descuento: ${cliente.descuento}%` : ''}
                    </div>
                `;
                
                if (cliente.descuento > 0) {
                    descuentoAplicado = cliente.descuento;
                    document.getElementById('descuento').value = descuentoAplicado;
                }
            }
        }
        
        // Add event listener to the empty cart button
        const emptyCartBtn = document.getElementById('empty-cart');
        if (emptyCartBtn) {
            emptyCartBtn.addEventListener('click', vaciarCarrito);
        }
        
    } catch (error) {
        console.error('Error initializing cart:', error);
        carrito = [];
    }
}

/**
 * Initialize product search functionality
 */
function initializeSearch() {
    const searchInput = document.getElementById('search-products');
    if (!searchInput) return;
    
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        // Clear previous timeout
        if (timeoutBusqueda) {
            clearTimeout(timeoutBusqueda);
        }
        
        // Set a new timeout to avoid too many requests
        timeoutBusqueda = setTimeout(() => {
            if (query.length >= 2) {
                buscarProductos(query);
            } else if (query.length === 0) {
                loadCategorias(); // If search is cleared, load categories
            }
        }, 300);
    });
    
    // Search button click
    const searchButton = document.getElementById('search-button');
    if (searchButton) {
        searchButton.addEventListener('click', function() {
            const query = searchInput.value.trim();
            if (query.length >= 2) {
                buscarProductos(query);
            }
        });
    }
}

/**
 * Initialize barcode scanner functionality
 */
function initializeBarcodeScanner() {
    // Listen for keyboard input for barcode scanner
    document.addEventListener('keydown', function(event) {
        // If the active element is an input or textarea, don't process as barcode
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }
        
        // If the key is Enter, process the accumulated input as a barcode
        if (event.key === 'Enter' && scannerInput.length > 0) {
            buscarProductoPorCodigo(scannerInput);
            scannerInput = '';
            return;
        }
        
        // Only add numeric or alphabetic characters to the scanner input
        if (/[0-9a-zA-Z]/.test(event.key) && event.key.length === 1) {
            scannerInput += event.key;
            
            // Reset the timeout
            if (scannerTimeout) {
                clearTimeout(scannerTimeout);
            }
            
            // Set a timeout to clear the input if no more keys are pressed
            scannerTimeout = setTimeout(() => {
                scannerInput = '';
            }, 100);
        }
    });
}

/**
 * Initialize customer selection functionality
 */
function initializeClienteSelection() {
    const clienteSelect = document.getElementById('cliente');
    if (!clienteSelect) return;
    
    clienteSelect.addEventListener('change', function() {
        const clienteId = this.value;
        if (clienteId) {
            fetch(`/api/clientes/${clienteId}/`)
                .then(response => response.json())
                .then(data => {
                    cliente = data;
                    localStorage.setItem('pos_cliente', JSON.stringify(cliente));
                    
                    // Display customer information
                    document.getElementById('cliente_info').innerHTML = `
                        <div class="alert alert-info">
                            <strong>${cliente.nombre}</strong>
                            ${cliente.descuento > 0 ? ` - Descuento: ${cliente.descuento}%` : ''}
                        </div>
                    `;
                    
                    // Apply customer discount if any
                    if (cliente.descuento > 0) {
                        descuentoAplicado = cliente.descuento;
                        document.getElementById('descuento').value = descuentoAplicado;
                    } else {
                        descuentoAplicado = 0;
                        document.getElementById('descuento').value = 0;
                    }
                    
                    // Recalculate totals
                    calcularTotales();
                })
                .catch(error => {
                    console.error('Error loading customer:', error);
                    mostrarAlerta('Error al cargar datos del cliente', 'danger');
                });
        } else {
            cliente = null;
            localStorage.removeItem('pos_cliente');
            document.getElementById('cliente_info').innerHTML = '';
            descuentoAplicado = 0;
            document.getElementById('descuento').value = 0;
            calcularTotales();
        }
    });
    
    // Manual discount input
    const descuentoInput = document.getElementById('descuento');
    if (descuentoInput) {
        descuentoInput.addEventListener('change', function() {
            descuentoAplicado = parseFloat(this.value) || 0;
            calcularTotales();
        });
    }
}

/**
 * Initialize payment processing functionality
 */
function initializePayment() {
    const procesarVentaBtn = document.getElementById('procesar-venta');
    if (!procesarVentaBtn) return;
    
    procesarVentaBtn.addEventListener('click', function() {
        procesarVenta();
    });
}

/**
 * Initialize keyboard shortcuts
 */
function initializeHotkeys() {
    document.addEventListener('keydown', function(event) {
        // If F2 is pressed, focus on search
        if (event.key === 'F2') {
            event.preventDefault();
            document.getElementById('search-products').focus();
        }
        
        // If F3 is pressed, focus on customer select
        if (event.key === 'F3') {
            event.preventDefault();
            document.getElementById('cliente').focus();
        }
        
        // If F4 is pressed, proceed to payment
        if (event.key === 'F4') {
            event.preventDefault();
            procesarVenta();
        }
        
        // If F5 is pressed, clear cart
        if (event.key === 'F5') {
            event.preventDefault();
            vaciarCarrito();
        }
    });
}

/**
 * Load product categories
 */
function loadCategorias() {
    const catalogContainer = document.getElementById('product-catalog');
    if (!catalogContainer) return;
    
    // Show loader
    catalogContainer.innerHTML = '<div class="text-center p-5"><div class="spinner-border text-primary"></div><p class="mt-2">Cargando categorías...</p></div>';
    
    fetch('/api/productos/categorias/')
        .then(response => response.json())
        .then(data => {
            let html = `
                <div class="mb-4">
                    <h5 class="mb-3">Categorías</h5>
                    <div class="row">
            `;
            
            data.forEach(categoria => {
                html += `
                    <div class="col-md-4 col-lg-3 mb-3">
                        <div class="card shadow-sm h-100 categoria-card" data-id="${categoria.id}" onclick="loadProductosByCategoria(${categoria.id}, '${categoria.nombre}')">
                            <div class="card-body text-center">
                                <i class="bi bi-tag-fill fs-1 mb-2 text-primary"></i>
                                <h6 class="card-title">${categoria.nombre}</h6>
                                <p class="card-text small text-muted">${categoria.producto_count} productos</p>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
            
            catalogContainer.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading categories:', error);
            catalogContainer.innerHTML = '<div class="alert alert-danger">Error al cargar categorías</div>';
        });
}

/**
 * Load products by category
 */
function loadProductosByCategoria(categoriaId, categoriaNombre) {
    const catalogContainer = document.getElementById('product-catalog');
    if (!catalogContainer) return;
    
    // Show loader
    catalogContainer.innerHTML = '<div class="text-center p-5"><div class="spinner-border text-primary"></div><p class="mt-2">Cargando productos...</p></div>';
    
    fetch(`/api/productos/?categoria=${categoriaId}&disponible=true&limit=100`)
        .then(response => response.json())
        .then(data => {
            let html = `
                <div class="mb-3">
                    <h5 class="d-flex justify-content-between align-items-center">
                        <span>${categoriaNombre}</span>
                        <button class="btn btn-sm btn-outline-secondary" onclick="loadCategorias()">
                            <i class="bi bi-arrow-left me-1"></i> Volver
                        </button>
                    </h5>
                </div>
                <div class="row">
            `;
            
            if (data.results && data.results.length > 0) {
                data.results.forEach(producto => {
                    html += `
                        <div class="col-md-4 col-lg-3 mb-3">
                            <div class="card h-100 shadow-sm producto-card" data-id="${producto.id}" onclick="seleccionarProducto(${JSON.stringify(producto).replace(/"/g, '&quot;')})">
                                <div class="card-body">
                                    <h6 class="card-title">${producto.nombre}</h6>
                                    <p class="card-text small text-muted">Código: ${producto.codigo}</p>
                                    <p class="card-text fw-bold text-primary">$${parseFloat(producto.precio_venta).toFixed(2)}</p>
                                </div>
                                <div class="card-footer bg-transparent text-end">
                                    <button class="btn btn-sm btn-primary" onclick="agregarAlCarrito(event, ${JSON.stringify(producto).replace(/"/g, '&quot;')})">
                                        <i class="bi bi-cart-plus"></i> Agregar
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                });
            } else {
                html += `
                    <div class="col-12">
                        <div class="alert alert-info">No hay productos disponibles en esta categoría</div>
                    </div>
                `;
            }
            
            html += `
                </div>
            `;
            
            catalogContainer.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading products:', error);
            catalogContainer.innerHTML = '<div class="alert alert-danger">Error al cargar productos</div>';
        });
}

/**
 * Search for products by name, code, etc.
 */
function buscarProductos(query) {
    const catalogContainer = document.getElementById('product-catalog');
    if (!catalogContainer) return;
    
    // Show loader
    catalogContainer.innerHTML = '<div class="text-center p-5"><div class="spinner-border text-primary"></div><p class="mt-2">Buscando productos...</p></div>';
    
    fetch(`/api/productos/?search=${encodeURIComponent(query)}&disponible=true&limit=100`)
        .then(response => response.json())
        .then(data => {
            let html = `
                <div class="mb-3">
                    <h5 class="d-flex justify-content-between align-items-center">
                        <span>Resultados para "${query}"</span>
                        <button class="btn btn-sm btn-outline-secondary" onclick="loadCategorias()">
                            <i class="bi bi-arrow-left me-1"></i> Volver
                        </button>
                    </h5>
                </div>
                <div class="row">
            `;
            
            if (data.results && data.results.length > 0) {
                data.results.forEach(producto => {
                    html += `
                        <div class="col-md-4 col-lg-3 mb-3">
                            <div class="card h-100 shadow-sm producto-card" data-id="${producto.id}" onclick="seleccionarProducto(${JSON.stringify(producto).replace(/"/g, '&quot;')})">
                                <div class="card-body">
                                    <h6 class="card-title">${producto.nombre}</h6>
                                    <p class="card-text small text-muted">Código: ${producto.codigo}</p>
                                    <p class="card-text fw-bold text-primary">$${parseFloat(producto.precio_venta).toFixed(2)}</p>
                                </div>
                                <div class="card-footer bg-transparent text-end">
                                    <button class="btn btn-sm btn-primary" onclick="agregarAlCarrito(event, ${JSON.stringify(producto).replace(/"/g, '&quot;')})">
                                        <i class="bi bi-cart-plus"></i> Agregar
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                });
            } else {
                html += `
                    <div class="col-12">
                        <div class="alert alert-info">No se encontraron productos que coincidan con "${query}"</div>
                    </div>
                `;
            }
            
            html += `
                </div>
            `;
            
            catalogContainer.innerHTML = html;
        })
        .catch(error => {
            console.error('Error searching products:', error);
            catalogContainer.innerHTML = '<div class="alert alert-danger">Error al buscar productos</div>';
        });
}

/**
 * Search for a product by its barcode
 */
function buscarProductoPorCodigo(codigo) {
    // Show a small notification that we're processing the barcode
    mostrarAlerta(`Procesando código: ${codigo}`, 'info', 1000);
    
    fetch(`/api/productos/?codigo=${encodeURIComponent(codigo)}&disponible=true`)
        .then(response => response.json())
        .then(data => {
            if (data.results && data.results.length > 0) {
                const producto = data.results[0];
                agregarAlCarrito(null, producto);
                
                // Show a success notification
                mostrarAlerta(`Producto agregado: ${producto.nombre}`, 'success');
            } else {
                // Show an error notification
                mostrarAlerta(`No se encontró producto con código: ${codigo}`, 'warning');
            }
        })
        .catch(error => {
            console.error('Error searching by code:', error);
            mostrarAlerta('Error al buscar producto por código', 'danger');
        });
}

/**
 * Select a product for detailed view
 */
function seleccionarProducto(producto) {
    productoSeleccionado = producto;
    
    // Show product details in a modal
    const modal = new bootstrap.Modal(document.getElementById('producto-modal'));
    
    document.getElementById('producto-nombre').textContent = producto.nombre;
    document.getElementById('producto-codigo').textContent = producto.codigo;
    document.getElementById('producto-precio').textContent = `$${parseFloat(producto.precio_venta).toFixed(2)}`;
    
    // Set initial quantity
    document.getElementById('producto-cantidad').value = 1;
    
    // Check inventory
    fetch(`/api/productos/${producto.id}/inventory/?tienda=${tiendaId}`)
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                const stock = data[0].cantidad;
                document.getElementById('producto-stock').textContent = stock;
                
                // Update max quantity allowed
                document.getElementById('producto-cantidad').max = stock;
            } else {
                document.getElementById('producto-stock').textContent = 'No disponible';
                document.getElementById('producto-cantidad').max = 0;
            }
        })
        .catch(error => {
            console.error('Error checking inventory:', error);
            document.getElementById('producto-stock').textContent = 'Error al verificar';
        });
    
    modal.show();
}

/**
 * Add a product to the cart
 */
function agregarAlCarrito(event, producto) {
    if (event) {
        event.stopPropagation();
    }
    
    let cantidad = 1;
    
    // If product was selected in the modal, get quantity from input
    if (productoSeleccionado && productoSeleccionado.id === producto.id) {
        cantidad = parseInt(document.getElementById('producto-cantidad').value) || 1;
        
        // Hide the modal if it's open
        const modalElement = document.getElementById('producto-modal');
        if (modalElement) {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) {
                modal.hide();
            }
        }
        
        productoSeleccionado = null;
    }
    
    // Check if product already exists in cart
    const index = carrito.findIndex(item => item.id === producto.id);
    
    if (index !== -1) {
        // Update quantity if product already in cart
        carrito[index].cantidad += cantidad;
        carrito[index].subtotal = carrito[index].cantidad * parseFloat(carrito[index].precio_venta);
    } else {
        // Add new product to cart
        carrito.push({
            id: producto.id,
            codigo: producto.codigo,
            nombre: producto.nombre,
            precio_venta: parseFloat(producto.precio_venta),
            cantidad: cantidad,
            subtotal: cantidad * parseFloat(producto.precio_venta)
        });
    }
    
    // Save cart to localStorage
    guardarCarrito();
    
    // Update cart view
    actualizarVista();
    
    // Show success message
    mostrarAlerta(`${producto.nombre} agregado al carrito`, 'success');
}

/**
 * Update cart item quantity
 */
function actualizarCantidad(index, cantidad) {
    if (index >= 0 && index < carrito.length) {
        carrito[index].cantidad = parseInt(cantidad);
        carrito[index].subtotal = carrito[index].cantidad * carrito[index].precio_venta;
        
        // Save cart to localStorage
        guardarCarrito();
        
        // Update cart view
        actualizarVista();
    }
}

/**
 * Remove item from cart
 */
function eliminarDelCarrito(index) {
    if (index >= 0 && index < carrito.length) {
        const producto = carrito[index];
        carrito.splice(index, 1);
        
        // Save cart to localStorage
        guardarCarrito();
        
        // Update cart view
        actualizarVista();
        
        // Show success message
        mostrarAlerta(`${producto.nombre} eliminado del carrito`, 'success');
    }
}

/**
 * Empty the cart
 */
function vaciarCarrito() {
    // Ask for confirmation
    if (carrito.length > 0 && !confirm('¿Estás seguro de vaciar el carrito?')) {
        return;
    }
    
    carrito = [];
    
    // Save cart to localStorage
    guardarCarrito();
    
    // Update cart view
    actualizarVista();
    
    // Show success message
    mostrarAlerta('Carrito vaciado', 'success');
}

/**
 * Save cart to localStorage
 */
function guardarCarrito() {
    localStorage.setItem('pos_carrito', JSON.stringify(carrito));
}

/**
 * Update cart view and totals
 */
function actualizarVista() {
    const carritoBody = document.getElementById('carrito-body');
    const carritoEmpty = document.getElementById('carrito-empty');
    const carritoTotals = document.getElementById('carrito-totals');
    const procesarVentaBtn = document.getElementById('procesar-venta');
    
    if (!carritoBody || !carritoEmpty || !carritoTotals) return;
    
    if (carrito.length > 0) {
        // Hide empty cart message
        carritoEmpty.classList.add('d-none');
        carritoTotals.classList.remove('d-none');
        
        if (procesarVentaBtn) {
            procesarVentaBtn.disabled = false;
        }
        
        // Generate cart items HTML
        let html = '';
        
        carrito.forEach((item, index) => {
            html += `
                <tr>
                    <td>${item.codigo}</td>
                    <td>${item.nombre}</td>
                    <td class="text-end">$${item.precio_venta.toFixed(2)}</td>
                    <td>
                        <div class="input-group input-group-sm">
                            <button class="btn btn-outline-secondary" type="button" 
                                    onclick="actualizarCantidad(${index}, ${Math.max(1, item.cantidad - 1)})">
                                <i class="bi bi-dash"></i>
                            </button>
                            <input type="number" class="form-control text-center" value="${item.cantidad}" min="1"
                                   onchange="actualizarCantidad(${index}, this.value)">
                            <button class="btn btn-outline-secondary" type="button"
                                    onclick="actualizarCantidad(${index}, ${item.cantidad + 1})">
                                <i class="bi bi-plus"></i>
                            </button>
                        </div>
                    </td>
                    <td class="text-end">$${item.subtotal.toFixed(2)}</td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-outline-danger" onclick="eliminarDelCarrito(${index})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        });
        
        carritoBody.innerHTML = html;
    } else {
        // Show empty cart message
        carritoEmpty.classList.remove('d-none');
        carritoTotals.classList.add('d-none');
        carritoBody.innerHTML = '';
        
        if (procesarVentaBtn) {
            procesarVentaBtn.disabled = true;
        }
    }
    
    // Calculate and update totals
    calcularTotales();
}

/**
 * Calculate and update cart totals
 */
function calcularTotales() {
    const subtotalElement = document.getElementById('subtotal');
    const descuentoElement = document.getElementById('descuento-valor');
    const totalElement = document.getElementById('total');
    
    if (!subtotalElement || !descuentoElement || !totalElement) return;
    
    // Calculate subtotal
    subTotal = carrito.reduce((total, item) => total + item.subtotal, 0);
    
    // Apply discount
    const descuentoValor = (subTotal * descuentoAplicado) / 100;
    
    // Calculate total
    totalVenta = subTotal - descuentoValor;
    
    // Update display
    subtotalElement.textContent = `$${subTotal.toFixed(2)}`;
    descuentoElement.textContent = `$${descuentoValor.toFixed(2)} (${descuentoAplicado}%)`;
    totalElement.textContent = `$${totalVenta.toFixed(2)}`;
}

/**
 * Process the sale
 */
function procesarVenta() {
    // Validate cart has items
    if (carrito.length === 0) {
        mostrarAlerta('El carrito está vacío', 'warning');
        return;
    }
    
    // Validate customer is selected
    if (!cliente) {
        mostrarAlerta('Debe seleccionar un cliente', 'warning');
        document.getElementById('cliente').focus();
        return;
    }
    
    // Show payment modal
    const modalPago = new bootstrap.Modal(document.getElementById('pago-modal'));
    
    // Update payment modal info
    document.getElementById('pago-total').textContent = `$${totalVenta.toFixed(2)}`;
    document.getElementById('pago-monto').value = totalVenta.toFixed(2);
    document.getElementById('pago-cambio').textContent = '$0.00';
    
    // Set focus on payment amount
    modalPago.show();
    setTimeout(() => {
        document.getElementById('pago-monto').focus();
        document.getElementById('pago-monto').select();
    }, 500);
    
    // Handle payment amount changes
    document.getElementById('pago-monto').addEventListener('input', function() {
        const pagoMonto = parseFloat(this.value) || 0;
        const cambio = Math.max(0, pagoMonto - totalVenta);
        document.getElementById('pago-cambio').textContent = `$${cambio.toFixed(2)}`;
        
        // Enable/disable complete button based on payment amount
        document.getElementById('completar-venta').disabled = pagoMonto < totalVenta;
    });
    
    // Handle payment form submission
    document.getElementById('pago-form').addEventListener('submit', function(event) {
        event.preventDefault();
        completarVenta();
    });
}

/**
 * Complete the sale and send to server
 */
function completarVenta() {
    // Disable button to prevent double submission
    const completarBtn = document.getElementById('completar-venta');
    completarBtn.disabled = true;
    completarBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando...';
    
    // Prepare data for the API
    const data = {
        cliente: cliente.id,
        tienda: tiendaId,
        tipo: 'venta',
        estado: 'completado',
        pagado: true,
        descuento_porcentaje: descuentoAplicado,
        total: totalVenta,
        detalles: carrito.map(item => ({
            producto: item.id,
            cantidad: item.cantidad,
            precio_unitario: item.precio_venta,
            subtotal: item.subtotal
        }))
    };
    
    // Call the API to create the order
    fetch('/api/ventas/pedidos/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(data)
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Close the payment modal
            const modalPago = bootstrap.Modal.getInstance(document.getElementById('pago-modal'));
            modalPago.hide();
            
            // Clear the cart
            carrito = [];
            guardarCarrito();
            actualizarVista();
            
            // Show success message
            mostrarAlerta('Venta completada exitosamente', 'success');
            
            // Display receipt or redirect to receipt page
            window.location.href = `/ventas/pedidos/${data.id}/`;
        })
        .catch(error => {
            console.error('Error completing sale:', error);
            mostrarAlerta('Error al procesar la venta: ' + error.message, 'danger');
            
            // Re-enable the button
            completarBtn.disabled = false;
            completarBtn.innerHTML = 'Completar Venta';
        });
}

/**
 * Helper function to show alerts
 */
function mostrarAlerta(mensaje, tipo = 'info', duracion = 3000) {
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    const id = 'alert-' + Date.now();
    const html = `
        <div id="${id}" class="alert alert-${tipo} alert-dismissible fade show" role="alert">
            ${mensaje}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    alertsContainer.innerHTML += html;
    
    // Auto-dismiss after duration
    setTimeout(() => {
        const alertElement = document.getElementById(id);
        if (alertElement) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, duracion);
}

/**
 * Get CSRF token for POST requests
 */
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length, cookie.length);
        }
    }
    return '';
}
