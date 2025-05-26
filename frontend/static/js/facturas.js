/**
 * facturas.js - JavaScript functions for the facturación (billing) functionality
 */

/**
 * Handles filtering in factura_list.html
 */
function initFacturaListFilters() {
    const form = document.getElementById('facturaFilterForm');
    if (!form) return;

    // Auto-submit form when date fields change
    const dateFields = form.querySelectorAll('input[type="date"]');
    dateFields.forEach(field => {
        field.addEventListener('change', () => {
            form.submit();
        });
    });

    // Clear filters button
    const clearBtn = document.getElementById('clearFiltersBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const today = new Date();
            const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
            
            document.getElementById('fecha_desde').value = firstDay.toISOString().split('T')[0];
            document.getElementById('fecha_hasta').value = today.toISOString().split('T')[0];
            document.getElementById('folio').value = '';
            
            form.submit();
        });
    }
}

/**
 * Function to handle print action in factura_print.html
 */
function printFactura() {
    window.print();
}

/**
 * Function to show loading indicator when generating PDF
 */
function showPdfLoading() {
    // Find all PDF download links
    const pdfLinks = document.querySelectorAll('a[href*="factura_pdf"]');
    
    pdfLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Change the icon to a spinner
            const icon = this.querySelector('i');
            if (icon) {
                icon.className = 'bi bi-arrow-repeat spin me-1';
            }
            
            // Add "Generando..." text
            this.innerHTML = this.innerHTML.replace('Descargar PDF', 'Generando PDF...');
        });
    });
}

/**
 * Initialize all factura related functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize filters in the factura list page
    initFacturaListFilters();
    
    // Add print button functionality
    const printBtn = document.getElementById('printFacturaBtn');
    if (printBtn) {
        printBtn.addEventListener('click', printFactura);
    }
    
    // Add loading indicator for PDF generation
    showPdfLoading();
});
