// Quick sidebar test
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Testing sidebar functionality...');
    
    const sidebar = document.getElementById('posSidebar');
    const toggle = document.getElementById('sidebarToggle');
    const mainContent = document.getElementById('mainContent');
    
    console.log('Sidebar element:', sidebar);
    console.log('Toggle button:', toggle);
    console.log('Main content:', mainContent);
    
    if (sidebar) {
        console.log('✅ Sidebar found');
        console.log('Sidebar classes:', sidebar.className);
    } else {
        console.log('❌ Sidebar not found');
    }
    
    if (toggle) {
        console.log('✅ Toggle button found');
        console.log('Toggle classes:', toggle.className);
        
        // Test toggle functionality
        toggle.addEventListener('click', function() {
            console.log('🖱️ Toggle button clicked!');
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('sidebar-collapsed');
            console.log('Sidebar toggled. New classes:', sidebar.className);
        });
    } else {
        console.log('❌ Toggle button not found');
    }
    
    // Force visibility
    document.body.style.opacity = '1';
    document.body.style.visibility = 'visible';
    
    console.log('✅ Sidebar test complete');
});
