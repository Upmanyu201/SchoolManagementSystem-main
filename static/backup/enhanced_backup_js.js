// Enhanced Backup JavaScript - Fallback Version
console.log('🔄 Enhanced Backup Fallback System Loading...');

// Simplified backup functions for fallback
window.enhancedBackupFallback = {
    
    // Simple CSRF token getter
    getCsrfToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return decodeURIComponent(value);
            }
        }
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || null;
    },
    
    // Simple toast notification
    showToast(message, type = 'info') {
        // Remove existing toasts
        document.querySelectorAll('.backup-toast').forEach(t => t.remove());
        
        const toast = document.createElement('div');
        toast.className = 'backup-toast fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm';
        
        const colors = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            info: 'bg-blue-500 text-white'
        };
        
        toast.className += ` ${colors[type] || colors.info}`;
        toast.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white">×</button>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    },
    
    // Enhanced restore function with better error handling
    async executeRestore(backupId) {
        try {
            const csrfToken = this.getCsrfToken();
            if (!csrfToken) {
                throw new Error('CSRF token not found. Please refresh the page.');
            }
            
            if (!confirm('Are you sure you want to restore this backup?')) {
                return;
            }
            
            this.showToast('Starting restore process...', 'info');
            
            const response = await fetch(`/backup/restore/history/${backupId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    restore_category: 'full',
                    restore_mode: 'merge'
                }),
                credentials: 'same-origin'
            });
            
            // Handle different response types
            let data;
            const contentType = response.headers.get('content-type');
            
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                // Handle HTML error pages
                const text = await response.text();
                console.error('Non-JSON response:', text.substring(0, 200));
                throw new Error(`Server returned HTML instead of JSON (Status: ${response.status})`);
            }
            
            if (response.ok && data.status === 'success') {
                this.showToast(data.message || 'Restore completed successfully!', 'success');
                
                // Show detailed results if available
                if (data.result) {
                    const result = data.result;
                    this.showToast(
                        `Restore summary: ${result.created || 0} created, ${result.updated || 0} updated, ${result.skipped || 0} skipped`,
                        'info'
                    );
                }
                
                if (typeof loadBackupHistory === 'function') {
                    loadBackupHistory();
                }
            } else {
                throw new Error(data.message || `Restore failed (Status: ${response.status})`);
            }
            
        } catch (error) {
            console.error('Restore error:', error);
            
            // Provide user-friendly error messages
            let userMessage = 'Restore failed. Please try again.';
            
            if (error.message.includes('CSRF')) {
                userMessage = 'Security token expired. Please refresh the page and try again.';
            } else if (error.message.includes('404')) {
                userMessage = 'Backup file not found. It may have been deleted.';
            } else if (error.message.includes('500')) {
                userMessage = 'Server error occurred. Please check the backup file and try again.';
            } else if (error.message.includes('HTML instead of JSON')) {
                userMessage = 'Server configuration error. Please contact your administrator.';
            }
            
            this.showToast(userMessage, 'error');
        }
    },
    
    // Simple history loader
    async loadHistory(showAll = false) {
        const tbody = document.getElementById('backupHistoryTableBody');
        if (!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="4" class="text-center py-4">Loading...</td></tr>';
        
        try {
            const response = await fetch(`/backup/history/?show_all=${showAll}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                let backups = [];
                
                // Handle different data structures
                if (Array.isArray(data.data)) {
                    backups = data.data;
                } else if (data.data && Array.isArray(data.data.backups)) {
                    backups = data.data.backups;
                } else if (data.data && typeof data.data === 'object') {
                    backups = Object.values(data.data).filter(item => 
                        item && typeof item === 'object' && item.id
                    );
                }
                
                if (backups.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="4" class="text-center py-8">No backups found</td></tr>';
                    return;
                }
                
                tbody.innerHTML = backups.map(backup => {
                    const date = new Date(backup.date || backup.created_at || Date.now()).toLocaleString();
                    const fileName = backup.file_name || backup.filename || `Backup ${backup.id}`;
                    
                    return `
                        <tr class="hover:bg-gray-50">
                            <td class="px-4 py-2">${fileName}</td>
                            <td class="px-4 py-2">${date}</td>
                            <td class="px-4 py-2">
                                <span class="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                                    ${backup.operation_type || backup.type || 'backup'}
                                </span>
                            </td>
                            <td class="px-4 py-2">
                                <button onclick="enhancedBackupFallback.executeRestore(${backup.id})" 
                                        class="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600">
                                    Restore
                                </button>
                            </td>
                        </tr>
                    `;
                }).join('');
                
            } else {
                throw new Error(data.message || 'Failed to load history');
            }
            
        } catch (error) {
            console.error('History loading error:', error);
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-8 text-red-500">
                        Error loading backup history: ${error.message}
                        <br>
                        <button onclick="enhancedBackupFallback.loadHistory(${showAll})" 
                                class="mt-2 bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600">
                            Try Again
                        </button>
                    </td>
                </tr>
            `;
        }
    }
};

// Initialize fallback system
console.log('✅ Enhanced Backup Fallback System loaded successfully');

// Auto-load history if DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (typeof enhancedBackupFallback !== 'undefined') {
                enhancedBackupFallback.loadHistory(false);
            }
        }, 1000);
    });
} else {
    setTimeout(() => {
        if (typeof enhancedBackupFallback !== 'undefined') {
            enhancedBackupFallback.loadHistory(false);
        }
    }, 1000);
}