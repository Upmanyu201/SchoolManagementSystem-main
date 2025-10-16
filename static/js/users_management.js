/**
 * Users Management JavaScript - Frontend Integration
 * Handles user management interactions with proper backend integration
 */

class UsersManager {
    constructor() {
        this.init();
    }

    init() {
        console.log('🚀 Users Management System Loading...');
        this.setupEventListeners();
        this.setupFormHandlers();
        console.log('✅ Users Management System Loaded');
    }

    setupEventListeners() {
        // Auto-submit on role filter change
        const roleSelect = document.querySelector('select[name="role"]');
        if (roleSelect) {
            roleSelect.addEventListener('change', function() {
                this.form.submit();
            });
        }

        // Setup clear cache buttons with proper binding
        document.querySelectorAll('.clear-cache-btn[data-clear-cache]').forEach(button => {
            const userId = button.getAttribute('data-clear-cache');
            button.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('🔄 Clear cache clicked for user:', userId);
                this.clearUserCache(userId);
            });
        });

        // Setup toggle status buttons with proper binding
        document.querySelectorAll('.toggle-status-btn[data-toggle-status]').forEach(button => {
            const userId = button.getAttribute('data-toggle-status');
            button.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('🔄 Toggle status clicked for user:', userId);
                this.toggleUserStatus(userId);
            });
        });

        console.log('✅ Event listeners setup complete');
        console.log('Clear cache buttons found:', document.querySelectorAll('.clear-cache-btn[data-clear-cache]').length);
        console.log('Toggle status buttons found:', document.querySelectorAll('.toggle-status-btn[data-toggle-status]').length);
    }

    setupFormHandlers() {
        // Enhanced form submission with loading states
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
                }
            });
        });
    }

    async clearUserCache(userId) {
        console.log('🔄 Starting clear cache for user:', userId);
        
        const modal = this.createConfirmationModal(
            'Clear User Cache',
            'This will clear all cached permissions for this user. Continue?',
            'orange'
        );

        const confirmBtn = modal.querySelector('.confirm-btn');
        confirmBtn.addEventListener('click', async () => {
            try {
                confirmBtn.disabled = true;
                confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Clearing...';

                console.log('🌐 Making request to:', `/users/clear-cache/${userId}/`);
                
                const response = await fetch(`/users/clear-cache/${userId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCSRFToken(),
                        'Content-Type': 'application/json'
                    }
                });

                console.log('📡 Response status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                console.log('📦 Response data:', data);

                if (data.success) {
                    this.showNotification(data.message || 'Cache cleared successfully!', 'success');
                } else {
                    this.showNotification(data.message || 'Error clearing cache', 'error');
                }

                this.closeModal(modal);
            } catch (error) {
                console.error('❌ Clear cache error:', error);
                this.showNotification(`Network error: ${error.message}`, 'error');
                this.closeModal(modal);
            }
        });
    }

    async toggleUserStatus(userId) {
        console.log('🔄 Starting toggle status for user:', userId);
        
        const button = document.querySelector(`.toggle-status-btn[data-toggle-status="${userId}"]`);
        const currentStatus = button.getAttribute('data-current-status') === 'true';
        const action = currentStatus ? 'deactivate' : 'activate';
        
        console.log('📊 Current status:', currentStatus, 'Action:', action);
        
        const modal = this.createConfirmationModal(
            `${action.charAt(0).toUpperCase() + action.slice(1)} User`,
            `Are you sure you want to ${action} this user?`,
            currentStatus ? 'red' : 'green'
        );

        const confirmBtn = modal.querySelector('.confirm-btn');
        confirmBtn.addEventListener('click', async () => {
            try {
                confirmBtn.disabled = true;
                confirmBtn.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>${action.charAt(0).toUpperCase() + action.slice(1)}ing...`;

                console.log('🌐 Making request to:', `/users/api/user-status/${userId}/`);
                
                const response = await fetch(`/users/api/user-status/${userId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCSRFToken(),
                        'Content-Type': 'application/json'
                    }
                });

                console.log('📡 Response status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                console.log('📦 Response data:', data);

                if (data.success) {
                    this.showNotification(data.message || `User ${action}d successfully!`, 'success');
                    // Update UI to reflect status change
                    setTimeout(() => location.reload(), 1000);
                } else {
                    this.showNotification(data.message || 'Error updating user status', 'error');
                }

                this.closeModal(modal);
            } catch (error) {
                console.error('❌ Toggle status error:', error);
                this.showNotification(`Network error: ${error.message}`, 'error');
                this.closeModal(modal);
            }
        });
    }

    createConfirmationModal(title, message, type = 'blue') {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 animate-fade-in';
        
        const colorClasses = {
            orange: 'bg-orange-100 text-orange-500 bg-orange-500 hover:bg-orange-600',
            red: 'bg-red-100 text-red-500 bg-red-500 hover:bg-red-600',
            blue: 'bg-blue-100 text-blue-500 bg-blue-500 hover:bg-blue-600'
        };

        const colors = colorClasses[type] || colorClasses.blue;
        const [iconBg, iconColor, btnBg, btnHover] = colors.split(' ');

        modal.innerHTML = `
            <div class="bg-white rounded-2xl p-8 max-w-md mx-4 shadow-2xl transform animate-slide-up">
                <div class="text-center">
                    <div class="w-16 h-16 ${iconBg} rounded-full flex items-center justify-center mx-auto mb-4">
                        <i class="fas fa-sync-alt ${iconColor} text-2xl"></i>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">${title}</h3>
                    <p class="text-gray-600 mb-6">${message}</p>
                    <div class="flex gap-3">
                        <button class="cancel-btn flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-xl hover:bg-gray-300 transition-colors">
                            Cancel
                        </button>
                        <button class="confirm-btn flex-1 px-4 py-2 ${btnBg} text-white rounded-xl ${btnHover} transition-colors">
                            Confirm
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Setup cancel button
        modal.querySelector('.cancel-btn').addEventListener('click', () => {
            this.closeModal(modal);
        });

        return modal;
    }

    closeModal(modal) {
        modal.classList.add('animate-fade-out');
        setTimeout(() => {
            if (modal.parentNode) {
                document.body.removeChild(modal);
            }
        }, 300);
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        
        const typeClasses = {
            success: 'bg-green-500 text-white fa-check-circle',
            error: 'bg-red-500 text-white fa-exclamation-circle',
            info: 'bg-blue-500 text-white fa-info-circle',
            warning: 'bg-yellow-500 text-white fa-exclamation-triangle'
        };

        const [bgClass, textClass, iconClass] = (typeClasses[type] || typeClasses.info).split(' ');

        notification.className = `fixed right-4 top-20 z-50 px-6 py-4 rounded-xl shadow-2xl transform translate-x-full transition-all duration-300 ${bgClass} ${textClass}`;
        
        notification.innerHTML = `
            <div class="flex items-center gap-3">
                <i class="fas ${iconClass}"></i>
                <span class="font-medium">${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    getCSRFToken() {
        // Try multiple ways to get CSRF token
        let token = document.querySelector('[name=csrfmiddlewaretoken]');
        if (token) return token.value;
        
        // Try from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') return value;
        }
        
        // Try from meta tag
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) return metaToken.getAttribute('content');
        
        console.error('CSRF token not found');
        return '';
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    new UsersManager();
});

// Add required CSS animations
const style = document.createElement('style');
style.textContent = `
    .animate-fade-in {
        animation: fadeIn 0.3s ease-out;
    }
    .animate-fade-out {
        animation: fadeOut 0.3s ease-out;
    }
    .animate-slide-up {
        animation: slideUp 0.3s ease-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px) scale(0.95); }
        to { opacity: 1; transform: translateY(0) scale(1); }
    }
`;
document.head.appendChild(style);

// Export for global access
window.UsersManager = UsersManager;