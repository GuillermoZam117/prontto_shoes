console.log('🔍 Simple dropdown test starting...');

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 DOM loaded, checking elements...');
    
    // Check if dropdown elements exist
    const dropdownToggles = document.querySelectorAll('.nav-dropdown-toggle');
    console.log('🔍 Found dropdown toggles:', dropdownToggles.length);
    
    dropdownToggles.forEach((toggle, index) => {
        const navText = toggle.querySelector('.nav-text');
        console.log(`🔍 Dropdown ${index + 1}: ${navText ? navText.textContent : 'No text found'}`);
        
        // Add a simple click handler for testing
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            console.log(`🖱️ Clicked on dropdown: ${navText ? navText.textContent : 'Unknown'}`);
            
            const dropdown = toggle.closest('.nav-dropdown');
            if (dropdown) {
                const isOpen = dropdown.classList.contains('open');
                console.log(`🔍 Dropdown is currently open: ${isOpen}`);
                
                // Close all dropdowns first
                document.querySelectorAll('.nav-dropdown').forEach(d => {
                    d.classList.remove('open');
                });
                
                // Open the clicked one if it wasn't open
                if (!isOpen) {
                    dropdown.classList.add('open');
                    console.log('✅ Dropdown opened');
                } else {
                    console.log('✅ Dropdown closed');
                }
            } else {
                console.log('❌ Could not find parent dropdown');
            }
        });
    });
});
