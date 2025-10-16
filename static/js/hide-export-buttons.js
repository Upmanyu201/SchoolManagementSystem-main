// Hide export buttons from specified templates
document.addEventListener('DOMContentLoaded', function() {
    // Get current page URL to determine which template we're on
    const currentPath = window.location.pathname;
    
    // Define templates that should have export buttons hidden
    const hideExportPaths = [
        '/teachers/',
        '/students/',
        '/transport/',
        '/student_fees/',
        '/fees/fees_setup/',
        '/fines/history/',
        '/attendance/'
    ];
    
    // Explicitly exclude backup pages from hiding export buttons
    const allowExportPaths = [
        '/backup/',
        '/reports/'
    ];
    
    // Check if current path matches any of the paths where exports should be hidden
    // But exclude paths that should always show export buttons
    const shouldHideExports = hideExportPaths.some(path => currentPath.includes(path)) && 
                             !allowExportPaths.some(path => currentPath.includes(path));
    
    if (shouldHideExports) {
        // Add class to body for CSS targeting
        document.body.classList.add('hide-exports');
        
        // Hide export buttons using JavaScript as backup
        const exportButtons = document.querySelectorAll([
            '.export-buttons',
            '[data-export]',
            'button[onclick*="exportData"]',
            'a[href*="export"]',
            'button[title*="Export"]',
            'button[title*="CSV"]',
            'button[title*="Excel"]',
            'button[title*="PDF"]'
        ].join(', '));
        
        exportButtons.forEach(button => {
            button.style.display = 'none';
        });
        
        console.log('Export buttons hidden for path:', currentPath);
    }
});