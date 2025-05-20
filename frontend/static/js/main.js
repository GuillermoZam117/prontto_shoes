/**
 * Archivo JavaScript principal para el Sistema POS Pronto Shoes
 * Versión minimalista para login
 */

console.log("Main.js loaded successfully");

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap si está disponible
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(function(tooltipTriggerEl) {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}); 