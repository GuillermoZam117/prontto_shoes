/**
 * Archivo JavaScript principal para el Sistema POS Pronto Shoes
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function(tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers de Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.forEach(function(popoverTriggerEl) {
        new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Inicializar select2 si está disponible
    if (typeof $.fn.select2 !== 'undefined') {
        $('.select2').select2({
            theme: 'bootstrap-5'
        });
    }
    
    // Funciones de utilidad global
    window.ProntoApp = {
        // Mostrar notificación con SweetAlert2
        notify: function(title, message, type) {
            Swal.fire({
                title: title,
                text: message,
                icon: type || 'info',
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000
            });
        },
        
        // Confirmar acción
        confirm: function(title, message, callback) {
            Swal.fire({
                title: title,
                text: message,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#0d6efd',
                cancelButtonColor: '#6c757d',
                confirmButtonText: 'Sí, continuar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed && typeof callback === 'function') {
                    callback();
                }
            });
        },
        
        // Formatear moneda
        formatCurrency: function(amount) {
            return new Intl.NumberFormat('es-MX', {
                style: 'currency',
                currency: 'MXN'
            }).format(amount);
        },
        
        // Formatear fecha
        formatDate: function(dateString) {
            const options = { year: 'numeric', month: 'long', day: 'numeric' };
            return new Date(dateString).toLocaleDateString('es-MX', options);
        }
    };
    
    // Manejo de eventos HTMX
    document.body.addEventListener('htmx:afterSwap', function(event) {
        // Reinicializar tooltips después de cargar contenido por HTMX
        var tooltipTriggerList = [].slice.call(event.detail.target.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(function(tooltipTriggerEl) {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Reinicializar select2 después de cargar contenido por HTMX
        if (typeof $.fn.select2 !== 'undefined') {
            $(event.detail.target).find('.select2').select2({
                theme: 'bootstrap-5'
            });
        }
    });
    
    // Manejo global de errores HTMX
    document.body.addEventListener('htmx:responseError', function(event) {
        console.error('Error HTMX:', event);
        
        let errorMessage = 'Ha ocurrido un error al procesar la solicitud.';
        
        if (event.detail.xhr.status === 403) {
            errorMessage = 'No tiene permisos para realizar esta acción.';
        } else if (event.detail.xhr.status === 404) {
            errorMessage = 'El recurso solicitado no fue encontrado.';
        } else if (event.detail.xhr.status === 500) {
            errorMessage = 'Error interno del servidor. Por favor, contacte al administrador.';
        }
        
        // Mostrar notificación de error
        Swal.fire({
            title: '¡Error!',
            text: errorMessage,
            icon: 'error',
        });
    });
}); 