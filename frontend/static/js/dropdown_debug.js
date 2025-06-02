// Dropdown Debug Script - Comprehensive Testing
console.log('🔍 Dropdown Debug Script Loading...');

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM Content Loaded - Starting Dropdown Debug');
    
    // Check if SidebarManager exists
    if (typeof SidebarManager !== 'undefined') {
        console.log('✅ SidebarManager class is available');
    } else {
        console.error('❌ SidebarManager class not found!');
        return;
    }
    
    // Check for dropdown elements
    const dropdownToggles = document.querySelectorAll('.nav-dropdown-toggle');
    const dropdowns = document.querySelectorAll('.nav-dropdown');
    
    console.log(`📊 Found ${dropdownToggles.length} dropdown toggles`);
    console.log(`📊 Found ${dropdowns.length} dropdown containers`);
    
    // Log each dropdown found
    dropdowns.forEach((dropdown, index) => {
        const toggle = dropdown.querySelector('.nav-dropdown-toggle');
        const menu = dropdown.querySelector('.nav-dropdown-menu');
        const text = toggle ? toggle.querySelector('.nav-text')?.textContent : 'Unknown';
        
        console.log(`📋 Dropdown ${index + 1}: "${text}"`);
        console.log(`  - Toggle element:`, toggle ? '✅' : '❌');
        console.log(`  - Menu element:`, menu ? '✅' : '❌');
        console.log(`  - Current classes:`, dropdown.className);
    });
    
    // Test manual dropdown toggle
    setTimeout(() => {
        console.log('🧪 Testing manual dropdown interaction...');
        
        dropdownToggles.forEach((toggle, index) => {
            const dropdownName = toggle.querySelector('.nav-text')?.textContent || `Dropdown ${index + 1}`;
            
            // Add manual click test
            console.log(`🖱️ Adding test click listener to: ${dropdownName}`);
            
            toggle.addEventListener('click', function(e) {
                console.log(`🎯 Manual click detected on: ${dropdownName}`);
                console.log('Event details:', {
                    target: e.target,
                    currentTarget: e.currentTarget,
                    preventDefault: e.defaultPrevented
                });
                
                const dropdown = this.closest('.nav-dropdown');
                console.log('Parent dropdown:', dropdown);
                console.log('Classes before toggle:', dropdown.className);
                
                // Test manual toggle
                dropdown.classList.toggle('open');
                console.log('Classes after manual toggle:', dropdown.className);
            });
        });
    }, 1000);
    
    // Check if SidebarManager instance exists
    setTimeout(() => {
        console.log('🔍 Checking for SidebarManager instance...');
        
        // Try to find the instance in window
        if (window.sidebarManager) {
            console.log('✅ Found window.sidebarManager instance');
        } else {
            console.log('❌ No window.sidebarManager instance found');
        }
        
        // Check if dropdowns are initialized
        const firstDropdown = document.querySelector('.nav-dropdown');
        if (firstDropdown) {
            console.log('🧪 Testing first dropdown manually...');
            console.log('Before click classes:', firstDropdown.className);
            
            // Simulate the SidebarManager toggle method
            const toggleMethod = function(dropdown) {
                const isOpen = dropdown.classList.contains('open');
                console.log(`Dropdown is currently: ${isOpen ? 'OPEN' : 'CLOSED'}`);
                
                if (isOpen) {
                    dropdown.classList.remove('open');
                    console.log('🔽 Closing dropdown');
                } else {
                    // Close other dropdowns
                    document.querySelectorAll('.nav-dropdown.open').forEach(other => {
                        if (other !== dropdown) {
                            other.classList.remove('open');
                            console.log('🔽 Closing other dropdown');
                        }
                    });
                    dropdown.classList.add('open');
                    console.log('🔼 Opening dropdown');
                }
                
                console.log('After toggle classes:', dropdown.className);
            };
            
            // Test the toggle method
            setTimeout(() => {
                console.log('🧪 Manual toggle test in 2 seconds...');
                toggleMethod(firstDropdown);
            }, 2000);
        }
    }, 1500);
});

// Monitor for any JavaScript errors
window.addEventListener('error', function(e) {
    console.error('🚨 JavaScript Error Detected:', {
        message: e.message,
        filename: e.filename,
        lineno: e.lineno,
        colno: e.colno,
        error: e.error
    });
});

console.log('🔍 Dropdown Debug Script Loaded Successfully');
