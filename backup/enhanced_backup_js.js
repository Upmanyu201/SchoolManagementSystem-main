// Enhanced Backup JavaScript with Better Error Handling and CSRF Management

// Enhanced CSRF token management
function getCsrfToken() {
    console.log('🔐 Getting CSRF token...');
    
    // First try to get from cookie
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
        console.log('🔐 CSRF token found in cookie:', cookieValue.substring(0, 8) + '...');
        return Promise.resolve(cookieValue);
    }
    
    // If no cookie, fetch from server
    console.log('🔐 No CSRF cookie found, fetching from server...');
    return fetch('/backup/csrf-token/', {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Failed to get CSRF token: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success' && data.csrf_token) {
            console.log('🔐 CSRF token fetched from server:', data.csrf_token.substring(0, 8) + '...');
            return data.csrf_token;
        } else {
            throw new Error('Invalid CSRF token response');
        }
    })
    .catch(error => {
        console.error('🔐 Failed to get CSRF token:', error);
        // Return null to indicate failure
        return null;
    });
}

// Enhanced error handling for restore operations
async function executeSmartHistoryRestoreEnhanced(backupId) {
    console.log('=== ENHANCED RESTORE START ===');
    console.log('🚀 executeSmartHistoryRestoreEnhanced called');
    console.log('📋 Backup ID:', backupId);
    console.log('🕐 Timestamp:', new Date().toISOString());
    
    try {
        // Get restore parameters
        const category = document.getElementById('modalRestoreCategory')?.value || 'full';
        const mode = document.getElementById('modalRestoreMode')?.value || 'merge';
        
        console.log('⚙️ Restore parameters:', {
            backupId: backupId,
            category: category,
            mode: mode,
            timestamp: new Date().toISOString()
        });
        
        // Close modal if exists
        if (typeof closeModal === 'function') {
            closeModal();
        }
        
        // Confirm operation
        const modeWarning = mode === 'replace' ? 
            'WARNING: Replace mode will delete existing data. Are you absolutely sure?' :
            'This will merge the backup data with your existing data. Continue?';
        
        if (!confirm(modeWarning)) {
            console.log('❌ User cancelled restore operation');
            return;
        }
        
        console.log('✅ User confirmed restore operation');
        showToast('Starting smart restore process...', 'info');
        
        // Get CSRF token
        const csrfToken = await getCsrfToken();
        if (!csrfToken) {
            throw new Error('Could not obtain CSRF token. Please refresh the page and try again.');
        }
        
        const requestUrl = `/backup/restore/history/${backupId}/`;
        const requestBody = {
            restore_category: category,
            restore_mode: mode
        };
        
        console.log('=== ENHANCED REQUEST DETAILS ===');
        console.log('🌐 Making POST request:', {
            url: requestUrl,
            method: 'POST',
            hasCSRFToken: !!csrfToken,
            csrfTokenLength: csrfToken ? csrfToken.length : 0,
            requestBody: requestBody
        });
        
        const response = await fetch(requestUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(requestBody),
            credentials: 'same-origin'
        });
        
        console.log('=== ENHANCED RESPONSE RECEIVED ===');
        console.log('📡 Response status:', response.status);
        console.log('📡 Response ok:', response.ok);
        console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()));
        
        // Handle different response types
        let responseData;
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            responseData = await response.json();
        } else {
            const responseText = await response.text();
            console.error('❌ Non-JSON response received:', responseText);
            
            // Try to extract error message from HTML
            if (responseText.includes('CSRF')) {
                throw new Error('CSRF token validation failed. Please refresh the page and try again.');
            } else if (responseText.includes('403')) {
                throw new Error('Access denied. Please check your permissions.');
            } else if (responseText.includes('500')) {
                throw new Error('Server error occurred. Please try again or contact support.');
            } else {
                throw new Error('Unexpected server response. Please try again.');
            }
        }
        
        console.log('📦 Response data:', responseData);
        
        if (!response.ok) {
            // Handle HTTP errors with better messages
            let errorMessage = 'Restore operation failed';
            
            if (response.status === 403) {
                errorMessage = 'Access denied. Please refresh the page and try again.';
            } else if (response.status === 404) {
                errorMessage = 'Backup file not found. It may have been deleted.';
            } else if (response.status === 500) {
                errorMessage = responseData?.message || 'Server error occurred during restore.';
            } else {
                errorMessage = responseData?.message || `HTTP ${response.status}: ${response.statusText}`;
            }
            
            throw new Error(errorMessage);
        }
        
        // Handle successful response
        if (responseData.status === 'success') {
            console.log('✅ Restore successful:', responseData);
            showToast(responseData.message || 'Restore completed successfully!', 'success');
            
            // Show detailed results if available
            if (responseData.summary) {
                const summary = responseData.summary;
                console.log('📊 Restore summary:', summary);
                showToast(`Restore completed: ${summary.created || 0} created, ${summary.updated || 0} updated, ${summary.skipped || 0} skipped`, 'info');
            }
            
            // Reload backup history
            if (typeof loadBackupHistory === 'function') {
                loadBackupHistory();
            }
        } else {
            console.error('❌ Restore failed:', responseData);
            throw new Error(responseData.message || 'Restore operation failed');
        }
        
    } catch (error) {
        console.error('=== ENHANCED ERROR CAUGHT ===');
        console.error('💥 Enhanced restore error:', {
            error: error,
            message: error.message,
            stack: error.stack,
            name: error.name,
            timestamp: new Date().toISOString()
        });
        
        // Show user-friendly error message
        let userMessage = 'We encountered an issue during restore. ';
        
        if (error.message.includes('CSRF')) {
            userMessage += 'Please refresh the page and try again.';
        } else if (error.message.includes('network') || error.message.includes('fetch')) {
            userMessage += 'Please check your internet connection and try again.';
        } else if (error.message.includes('permissions') || error.message.includes('Access denied')) {
            userMessage += 'You may not have permission to perform this action.';
        } else {
            userMessage += error.message || 'Please try again or contact support.';
        }
        
        showToast(userMessage, 'error');
        
    } finally {
        console.log('=== ENHANCED RESTORE END ===');
        console.log('🏁 Request completed at:', new Date().toISOString());
    }
}

// Enhanced toast notification system
function showToastEnhanced(message, type = 'info', duration = 5000) {
    // Remove existing toasts of the same type
    const existingToasts = document.querySelectorAll(`.toast-${type}`);
    existingToasts.forEach(toast => toast.remove());
    
    const toast = document.createElement('div');
    toast.className = `toast-${type} fixed top-4 right-4 z-50 p-4 rounded-xl shadow-lg animate-slide-in max-w-md`;
    
    // Set colors based on type
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
    
    // Auto-remove after duration
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

// Enhanced backup history loading with retry mechanism
async function loadBackupHistoryEnhanced(showingAll = false, retryCount = 0) {
    console.log('📚 Enhanced loadBackupHistory called with showingAll:', showingAll, 'retry:', retryCount);
    
    const tbody = document.getElementById('backupHistoryTableBody');
    const statusText = document.getElementById('historyStatusText');
    const showAllBtn = document.getElementById('showAllBtn');
    
    if (!tbody) {
        console.error('❌ Required DOM elements not found');
        return;
    }
    
    // Show loading state
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
        const historyUrl = `/backup/history/?show_all=${showingAll}`;
        console.log('🌐 Fetching backup history from:', historyUrl);
        
        const response = await fetch(historyUrl, {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        console.log('📡 History response:', {
            status: response.status,
            statusText: response.statusText,
            ok: response.ok,
            url: response.url
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('📦 History data received:', data);
        
        if (data.status === 'success') {
            console.log('✅ History loaded successfully, records count:', data.data.length);
            
            if (data.data.length === 0) {
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
            
            // Render backup records
            tbody.innerHTML = data.data.map(backup => {
                const date = new Date(backup.date).toLocaleString();
                const typeClass = backup.operation_type === 'backup' ? 'badge-success' : 'badge-info';
                
                return `
                    <tr class="hover:bg-gradient-to-r hover:from-purple-50 hover:to-indigo-50 transition-all duration-300">
                        <td class="px-6 py-4 font-medium text-gray-900">${backup.file_name}</td>
                        <td class="px-6 py-4 text-gray-700">${date}</td>
                        <td class="px-6 py-4"><span class="badge ${typeClass}">${backup.operation_type}</span></td>
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
            
            // Update status text and button
            if (statusText) {
                statusText.textContent = showingAll ? 
                    `Showing all ${data.data.length} backup files` : 
                    'Showing your 5 most recent backups';
            }
            
            if (showAllBtn) {
                showAllBtn.innerHTML = showingAll ? 
                    '<i class="fas fa-compress mr-2"></i>Show Less' : 
                    '<i class="fas fa-list mr-2"></i>Show All';
            }
            
            console.log('✅ Enhanced history table rendered successfully');
            
        } else {
            throw new Error(data.message || 'Failed to load backup history');
        }
        
    } catch (error) {
        console.error('💥 Enhanced history loading error:', error);
        
        // Show retry option for network errors
        const canRetry = retryCount < 3 && (
            error.message.includes('fetch') || 
            error.message.includes('network') || 
            error.message.includes('timeout')
        );
        
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="px-6 py-12 text-center">
                    <div class="flex flex-col items-center">
                        <i class="fas fa-exclamation-triangle text-4xl text-red-300 mb-4"></i>
                        <p class="text-red-500 mb-4">We're having trouble loading your backup history.</p>
                        <p class="text-gray-600 text-sm mb-4">${error.message}</p>
                        <div class="flex gap-2">
                            <button onclick="loadBackupHistoryEnhanced(${showingAll}, 0)" 
                                    class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors">
                                <i class="fas fa-sync-alt mr-2"></i>Try Again
                            </button>
                            ${canRetry ? `
                                <button onclick="loadBackupHistoryEnhanced(${showingAll}, ${retryCount + 1})" 
                                        class="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors">
                                    <i class="fas fa-redo mr-2"></i>Retry (${3 - retryCount} left)
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </td>
            </tr>
        `;
        
        // Auto-retry for network errors
        if (canRetry) {
            setTimeout(() => {
                loadBackupHistoryEnhanced(showingAll, retryCount + 1);
            }, 2000 * (retryCount + 1)); // Exponential backoff
        }
    }
}

// Initialize enhanced backup system
function initializeEnhancedBackupSystem() {
    console.log('🚀 Initializing enhanced backup system...');
    
    // Replace existing functions with enhanced versions
    window.showToast = showToastEnhanced;
    window.loadBackupHistory = loadBackupHistoryEnhanced;
    window.executeSmartHistoryRestore = executeSmartHistoryRestoreEnhanced;
    
    // Load backup history on initialization
    loadBackupHistoryEnhanced(false);
    
    console.log('✅ Enhanced backup system initialized');
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeEnhancedBackupSystem);
} else {
    initializeEnhancedBackupSystem();
}