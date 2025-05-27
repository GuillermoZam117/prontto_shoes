// Enhanced error tracking for the POS system
console.log('Loading enhanced error tracker...');

// Track all network requests to detect missing files
const originalFetch = window.fetch;
window.fetch = function(...args) {
    console.log('Fetch request:', args[0]);
    return originalFetch.apply(this, args)
        .then(response => {
            if (!response.ok) {
                console.error('Fetch failed:', {
                    url: args[0],
                    status: response.status,
                    statusText: response.statusText
                });
            }
            return response;
        })
        .catch(error => {
            console.error('Fetch error:', {
                url: args[0],
                error: error.message
            });
            throw error;
        });
};

// Track script loading errors
document.addEventListener('DOMContentLoaded', function() {
    // Monitor all script tags
    const scripts = document.querySelectorAll('script[src]');
    scripts.forEach(script => {
        script.addEventListener('error', function() {
            console.error('Script failed to load:', script.src);
        });
        script.addEventListener('load', function() {
            console.log('Script loaded successfully:', script.src);
        });
    });
});

// Monitor for h1-check specifically
window.addEventListener('error', function(e) {
    if (e.filename && e.filename.includes('h1-check')) {
        console.error('h1-check.js error detected:', {
            message: e.message,
            filename: e.filename,
            line: e.lineno,
            column: e.colno
        });
        
        // Try to identify the source
        console.log('Investigating h1-check.js source...');
        console.log('All scripts on page:');
        document.querySelectorAll('script').forEach(script => {
            console.log('Script:', script.src || 'inline', script.innerHTML.substring(0, 100));
        });
    }
});

// Check for detectStore function references
setTimeout(() => {
    console.log('Checking for detectStore references...');
    
    // Check if any global objects have detectStore
    for (let key in window) {
        try {
            if (window[key] && typeof window[key] === 'object' && window[key].detectStore) {
                console.log('Found detectStore in:', key, window[key]);
            }
        } catch (e) {
            // Ignore access errors
        }
    }
    
    // Check for Alpine.js store detection
    if (window.Alpine) {
        console.log('Alpine.js is present:', window.Alpine);
    }
    
    // Check for any third-party extensions or tools
    console.log('Browser extensions check:');
    if (navigator.webdriver) {
        console.log('WebDriver detected');
    }
    
}, 2000);

console.log('Enhanced error tracker loaded');
