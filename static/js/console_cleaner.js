// Console Cleaner - Suppress browser extension errors
(function() {
    'use strict';
    
    // Override console.error to filter extension errors
    const originalError = console.error;
    console.error = function(...args) {
        const message = args[0];
        
        // Skip browser extension errors
        if (typeof message === 'string' && 
            (message.includes('Could not establish connection') ||
             message.includes('contentScript.js') ||
             message.includes('Receiving end does not exist'))) {
            return; // Suppress these errors
        }
        
        // Log all other errors normally
        originalError.apply(console, args);
    };
})();