// Enhanced Backup JavaScript - Fixed Version
console.log('🚀 Enhanced Backup System Loading...');

// Enhanced CSRF token management
function getCsrfToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 10) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    
    if (cookieValue) {
        return Promise.resolve(cookieValue);
    }
    
    return fetch('/backup/csrf-token/', {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => data.csrf_token)
    .catch(() => null);
}

// Enhanced restore function
async function executeSmartHistoryRestoreEnhanced(backupId) {
    console.log('🚀 Starting enhanced restore for backup ID:', backupId);
    
    try {
        const category = document.getElementById('modalRestoreCategory')?.value || 'full';
        const mode = document.getElementById('modalRestoreMode')?.value || 'merge';
        
        if (typeof closeModal === 'function') {
            closeModal();
        }
        
        const modeWarning = mode === 'replace' ? 
            'WARNING: Replace mode will delete existing data. Are you absolutely sure?' :
            'This will merge the backup data with your existing data. Continue?';
        
        if (!confirm(modeWarning)) {
            return;
        }
        
        showToast('Starting smart restore process...', 'info');
        
        const csrfToken = await getCsrfToken();
        if (!csrfToken) {
            throw new Error('Could not obtain CSRF token. Please refresh the page and try again.');
        }
        
        const response = await fetch(`/backup/restore/history/${backupId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                restore_category: category,
                restore_mode: mode
            }),
            credentials: 'same-origin'
        });
        
        const responseData = await response.json();
        
        if (!response.ok) {
            throw new Error(responseData?.message || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        if (responseData.status === 'success') {
            showToast(responseData.message || 'Restore completed successfully!', 'success');
            if (typeof loadBackupHistory === 'function') {
                loadBackupHistory();
            }
        } else {
            throw new Error(responseData.message || 'Restore operation failed');
        }
        
    } catch (error) {
        console.error('💥 Enhanced restore error:', error);
        showToast(error.message || 'Restore failed. Please try again.', 'error');
    }
}

// Enhanced toast notifications
function showToastEnhanced(message, type = 'info', duration = 5000) {
    const existingToasts = document.querySelectorAll(`.toast-${type}`);
    existingToasts.forEach(toast => toast.remove());
    
    const toast = document.createElement('div');
    toast.className = `toast-${type} fixed top-4 right-4 z-50 p-4 rounded-xl shadow-lg max-w-md`;
    
    const colors = {
        success: 'bg-green-500 text-white',
        error: 'bg-red-500 text-white',
        warning: 'bg-yellow-500 text-black',
        info: 'bg-blue-500 text-white'
    };
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    toast.className += ` ${colors[type] || colors.info}`;
    
    toast.innerHTML = `
        <div class="flex items-start">
            <i class="fas ${icons[type] || icons.info} mr-3 mt-1 flex-shrink-0"></i>
            <div class="flex-1">
                <span class="font-medium">${message}</span>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-3 text-white hover:text-gray-200 flex-shrink-0">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 500);
        }
    }, duration);
}

// Enhanced backup history loading - FIXED DATA MAPPING
async function loadBackupHistoryEnhanced(showingAll = false) {
    console.log('📚 Enhanced loadBackupHistory called with showingAll:', showingAll);
    
    const tbody = document.getElementById('backupHistoryTableBody');
    const statusText = document.getElementById('historyStatusText');
    const showAllBtn = document.getElementById('showAllBtn');
    
    if (!tbody) {
        console.error('❌ Required DOM elements not found');
        return;
    }
    
    tbody.innerHTML = `
        <tr>
            <td colspan="4" class="px-6 py-12 text-center">
                <div class="flex flex-col items-center">
                    <i class="fas fa-spinner fa-spin text-4xl text-gray-300 mb-4"></i>
                    <p class="text-gray-500">Loading your backup archive...</p>
                </div>
            </td>
        </tr>
    `;
    
    try {
        const response = await fetch(`/backup/history/?show_all=${showingAll}`, {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📦 History data received:', data);
        
        if (data.status === 'success') {
            // FIX: Handle different data structures
            let backupList = [];
            
            if (Array.isArray(data.data)) {
                backupList = data.data;
            } else if (data.data && Array.isArray(data.data.backups)) {
                backupList = data.data.backups;
            } else if (data.data && typeof data.data === 'object') {
                // Convert object to array if needed
                backupList = Object.values(data.data).filter(item => 
                    item && typeof item === 'object' && item.id
                );
            }
            
            console.log('✅ Processed backup list:', backupList);
            
            if (backupList.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="4" class="px-6 py-12 text-center">
                            <div class="flex flex-col items-center">
                                <i class="fas fa-folder-open text-4xl text-gray-300 mb-4"></i>
                                <p class="text-gray-500">No backup files found. Create your first backup above!</p>
                            </div>
                        </td>
                    </tr>
                `;
                return;
            }
            
            tbody.innerHTML = backupList.map(backup => {
                const date = new Date(backup.date || backup.created_at || Date.now()).toLocaleString();
                const typeClass = (backup.operation_type || backup.type) === 'backup' ? 'badge-success' : 'badge-info';
                const fileName = backup.file_name || backup.filename || `Backup ${backup.id}`;
                
                return `
                    <tr class="hover:bg-gradient-to-r hover:from-purple-50 hover:to-indigo-50 transition-all duration-300">
                        <td class="px-6 py-4 font-medium text-gray-900">${fileName}</td>
                        <td class="px-6 py-4 text-gray-700">${date}</td>
                        <td class="px-6 py-4"><span class="badge ${typeClass}">${backup.operation_type || backup.type || 'backup'}</span></td>
                        <td class="px-6 py-4">
                            <div class="flex gap-2">
                                <button onclick="executeSmartHistoryRestoreEnhanced(${backup.id})" 
                                        class="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-3 py-2 rounded-lg transition-all duration-300 transform hover:scale-105 shadow-md" 
                                        title="Smart Restore">
                                    <i class="fas fa-magic"></i>
                                </button>
                                <button onclick="deleteBackup(${backup.id})" 
                                        class="bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white px-3 py-2 rounded-lg transition-all duration-300 transform hover:scale-105 shadow-md" 
                                        title="Delete this backup">
                                    <i class="fas fa-trash-alt"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
            
            if (statusText) {
                statusText.textContent = showingAll ? 
                    `Showing all ${backupList.length} backup files` : 
                    'Showing your 5 most recent backups';
            }
            
            if (showAllBtn) {
                showAllBtn.innerHTML = showingAll ? 
                    '<i class="fas fa-compress mr-2"></i>Show Less' : 
                    '<i class="fas fa-list mr-2"></i>Show All';
            }
            
        } else {
            throw new Error(data.message || 'Failed to load backup history');
        }
        
    } catch (error) {
        console.error('💥 Enhanced history loading error:', error);
        
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="px-6 py-12 text-center">
                    <div class="flex flex-col items-center">
                        <i class="fas fa-exclamation-triangle text-4xl text-red-300 mb-4"></i>
                        <p class="text-red-500 mb-4">We're having trouble loading your backup history.</p>
                        <p class="text-gray-600 text-sm mb-4">${error.message}</p>
                        <button onclick="loadBackupHistoryEnhanced(${showingAll})" 
                                class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors">
                            <i class="fas fa-sync-alt mr-2"></i>Try Again
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }
}

// Initialize enhanced backup system
function initializeEnhancedBackupSystem() {
    console.log('🚀 Initializing enhanced backup system...');
    
    // Replace existing functions with enhanced versions
    window.showToast = showToastEnhanced;
    window.loadBackupHistory = loadBackupHistoryEnhanced;
    window.executeSmartHistoryRestore = executeSmartHistoryRestoreEnhanced;
    
    console.log('✅ Enhanced backup system initialized');
}

// Auto-initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEnhancedBackupSystem);
} else {
    initializeEnhancedBackupSystem();
}

console.log('✅ Enhanced Backup JavaScript loaded successfully');