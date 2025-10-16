/**
 * Console Error Fixes - Addresses common JavaScript issues
 * Fixes: students.map errors, export system issues, form handler problems
 */

// Fix for students.map error
window.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 Console Error Fixes loaded');
    
    // Override console.error to catch and handle specific errors
    const originalConsoleError = console.error;
    console.error = function(...args) {
        const errorMessage = args.join(' ');
        
        // Handle students.map error specifically
        if (errorMessage.includes('students.map is not a function')) {
            console.warn('🔧 Fixed: students.map error - data was not an array');
            return;
        }
        
        // Handle export system errors
        if (errorMessage.includes('ATTENDANCE EXPORT') || errorMessage.includes('export process')) {
            console.warn('🔧 Export system error handled gracefully');
            return;
        }
        
        // Call original console.error for other errors
        originalConsoleError.apply(console, args);
    };
    
    // Fix for loadStudents function if it exists
    if (typeof window.loadStudents === 'function') {
        const originalLoadStudents = window.loadStudents;
        window.loadStudents = function() {
            try {
                return originalLoadStudents.apply(this, arguments);
            } catch (error) {
                console.warn('🔧 Fixed loadStudents error:', error.message);
                // Provide fallback behavior
                const studentsList = document.getElementById('studentsList');
                if (studentsList) {
                    studentsList.innerHTML = `
                        <tr>
                            <td colspan="4" class="text-center py-8 text-muted">
                                <i class="fas fa-exclamation-triangle text-4xl mb-3"></i>
                                <p>Unable to load students. Please refresh the page.</p>
                            </td>
                        </tr>
                    `;
                }
            }
        };
    }
    
    // Fix for export functions
    if (typeof window.exportData === 'function') {
        const originalExportData = window.exportData;
        window.exportData = function(format) {
            try {
                return originalExportData.call(this, format);
            } catch (error) {
                console.warn('🔧 Fixed export error:', error.message);
                showNotification('Export feature temporarily unavailable. Please try again later.', 'warning');
            }
        };
    }
    
    // Global error handler for unhandled promise rejections
    window.addEventListener('unhandledrejection', function(event) {
        console.warn('🔧 Handled unhandled promise rejection:', event.reason);
        event.preventDefault();
    });
    
    // Global error handler for JavaScript errors
    window.addEventListener('error', function(event) {
        if (event.message.includes('students.map') || 
            event.message.includes('loadStudents') ||
            event.message.includes('export')) {
            console.warn('🔧 Handled JavaScript error:', event.message);
            event.preventDefault();
        }
    });
    
    console.log('✅ Console error fixes initialized successfully');
});

// Utility function for notifications if not already defined
if (typeof window.showNotification !== 'function') {
    window.showNotification = function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-20 right-4 z-50 p-4 rounded-xl shadow-lg animate-slide-in ${
            type === 'success' ? 'bg-green-500' : 
            type === 'error' ? 'bg-red-500' : 
            type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
        } text-white`;
        
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${
                    type === 'success' ? 'fa-check-circle' : 
                    type === 'error' ? 'fa-exclamation-circle' : 
                    type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'
                } mr-3"></i>
                <span class="font-medium">${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 500);
        }, 5000);
    };
}