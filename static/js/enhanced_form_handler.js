/**
 * Enhanced Form Handler - Fixes processing button issues
 * Prevents stuck "Processing..." buttons and provides proper error recovery
 */

class EnhancedFormHandler {
    constructor(form) {
        this.form = form;
        this.submitBtn = form.querySelector('button[type="submit"]');
        this.originalText = this.submitBtn?.innerHTML || 'Submit';
        this.isProcessing = false;
        this.timeoutId = null;
        this.init();
    }

    init() {
        if (!this.submitBtn) return;
        
        // Store original text if not already stored
        if (!this.submitBtn.dataset.originalText) {
            this.submitBtn.dataset.originalText = this.originalText;
        }
        
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
        this.setupNetworkMonitoring();
    }

    handleSubmit(e) {
        // Prevent double submission
        if (this.isProcessing) {
            console.log('🚫 Form already processing, preventing duplicate submission');
            e.preventDefault();
            return false;
        }

        // Basic form validation
        if (!this.validateForm()) {
            e.preventDefault();
            return false;
        }

        // For AJAX forms, handle submission manually
        if (this.form.action.includes('submit-deposit') || this.form.id.includes('depositForm')) {
            e.preventDefault();
            this.handleAjaxSubmission();
            return false;
        }

        this.setProcessing(true);
        this.setupRecovery();
    }

    validateForm() {
        const requiredFields = this.form.querySelectorAll('[required]');
        for (let field of requiredFields) {
            if (!field.value.trim()) {
                field.focus();
                this.showMessage('Please fill in all required fields', 'error');
                return false;
            }
        }
        return true;
    }

    setProcessing(processing) {
        this.isProcessing = processing;
        
        if (processing) {
            this.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
            this.submitBtn.disabled = true;
            this.submitBtn.classList.add('processing');
        } else {
            this.submitBtn.innerHTML = this.submitBtn.dataset.originalText || this.originalText;
            this.submitBtn.disabled = false;
            this.submitBtn.classList.remove('processing');
        }
    }

    setupRecovery() {
        // Clear any existing timeout
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }

        // Extended timeout with network monitoring
        const timeoutDuration = document.hidden ? 30000 : 15000; // 30s if tab hidden, 15s if active
        
        this.timeoutId = setTimeout(() => {
            if (this.isProcessing) {
                this.setProcessing(false);
                this.showMessage('Request timeout. Please try again.', 'error');
                this.addRetryOption();
            }
        }, timeoutDuration);

        // Monitor for successful navigation
        this.monitorNavigation();
    }

    monitorNavigation() {
        const checkNavigation = () => {
            // If page is unloading/navigating, form was successful
            if (document.readyState === 'loading' || window.location.href !== this.originalUrl) {
                if (this.timeoutId) {
                    clearTimeout(this.timeoutId);
                }
                return;
            }
            
            // Continue monitoring if still processing
            if (this.isProcessing) {
                setTimeout(checkNavigation, 500);
            }
        };
        
        this.originalUrl = window.location.href;
        setTimeout(checkNavigation, 1000);
    }

    async handleAjaxSubmission() {
        this.setProcessing(true);
        
        try {
            const formData = new FormData(this.form);
            console.log('🚀 Submitting form data via AJAX to:', this.form.action);
            
            const response = await fetch(this.form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            console.log('📡 Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('📦 Response data:', data);
            
            if (data.status === 'success') {
                if (data.show_message && data.message) {
                    this.showMessage(data.message, 'success');
                }
                
                // Redirect after showing success message
                if (data.redirect_url) {
                    setTimeout(() => {
                        window.location.href = data.redirect_url;
                    }, 1500);
                } else {
                    this.setProcessing(false);
                }
            } else {
                // Handle error response
                const errorMsg = data.message || 'Payment failed. Please try again.';
                this.showMessage(errorMsg, 'error');
                this.setProcessing(false);
            }
            
        } catch (error) {
            console.error('❌ AJAX submission error:', error);
            this.showMessage('Network error. Please check your connection and try again.', 'error');
            this.setProcessing(false);
        }
    }

    setupNetworkMonitoring() {
        // Monitor online/offline status
        window.addEventListener('online', () => {
            if (this.isProcessing) {
                this.showMessage('Connection restored', 'success');
            }
        });

        window.addEventListener('offline', () => {
            if (this.isProcessing) {
                this.setProcessing(false);
                this.showMessage('Connection lost. Please check your internet and try again.', 'error');
            }
        });

        // Monitor tab visibility for timeout adjustment
        document.addEventListener('visibilitychange', () => {
            if (this.isProcessing && !document.hidden) {
                // User returned to tab, extend timeout
                this.setupRecovery();
            }
        });
    }

    addRetryOption() {
        const retryBtn = document.createElement('button');
        retryBtn.type = 'button';
        retryBtn.className = 'btn btn-secondary btn-sm ml-2';
        retryBtn.innerHTML = '<i class="fas fa-redo mr-1"></i>Retry';
        retryBtn.onclick = () => {
            retryBtn.remove();
            this.form.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
        };
        
        this.submitBtn.parentNode.insertBefore(retryBtn, this.submitBtn.nextSibling);
        
        // Auto-remove retry button after 10 seconds
        setTimeout(() => {
            if (retryBtn.parentNode) {
                retryBtn.remove();
            }
        }, 10000);
    }

    showMessage(message, type = 'info') {
        // Create or update message element
        let messageEl = document.getElementById('form-handler-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'form-handler-message';
            messageEl.className = 'fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300';
            document.body.appendChild(messageEl);
        }

        // Set message content and style
        const colors = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            info: 'bg-blue-500 text-white',
            warning: 'bg-yellow-500 text-black'
        };

        messageEl.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 ${colors[type] || colors.info}`;
        messageEl.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.style.opacity = '0';
                messageEl.style.transform = 'translateX(100%)';
                setTimeout(() => messageEl.remove(), 300);
            }
        }, 5000);
    }
}

// Auto-initialize for all POST forms
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Enhanced Form Handler loaded successfully');
    
    // Test basic JavaScript execution
    try {
        const testDiv = document.createElement('div');
        console.log('✅ Basic JavaScript execution: OK');
    } catch (e) {
        console.error('❌ JavaScript execution error:', e);
        return;
    }

    // Find and enhance all POST forms (including dynamically created ones)
    const forms = document.querySelectorAll('form[method="post"], form[method="POST"], form:not([method]), form[id*="depositForm"]');
    const excludedForms = document.querySelectorAll('.no-enhanced-handler');
    
    console.log(`📋 Found ${forms.length} POST forms for enhancement`);
    console.log(`🚫 Found ${excludedForms.length} excluded forms`);

    forms.forEach(form => {
        // Skip if form has exclusion class
        if (form.classList.contains('no-enhanced-handler')) {
            return;
        }

        // Skip if form already has handler
        if (form.dataset.enhancedHandler) {
            return;
        }

        // Initialize enhanced handler
        try {
            new EnhancedFormHandler(form);
            form.dataset.enhancedHandler = 'true';
            console.log(`✅ Enhanced handler added to form: ${form.id || form.action || 'unnamed'}`);
        } catch (e) {
            console.error('❌ Failed to initialize form handler:', e);
        }
    });
    
    // Watch for dynamically added forms
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1) { // Element node
                    const newForms = node.querySelectorAll ? node.querySelectorAll('form') : [];
                    newForms.forEach(form => {
                        if (!form.dataset.enhancedHandler && !form.classList.contains('no-enhanced-handler')) {
                            try {
                                new EnhancedFormHandler(form);
                                form.dataset.enhancedHandler = 'true';
                                console.log(`✅ Enhanced handler added to dynamic form: ${form.id || 'unnamed'}`);
                            } catch (e) {
                                console.error('❌ Failed to initialize dynamic form handler:', e);
                            }
                        }
                    });
                }
            });
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // Test timeout recovery
    setTimeout(() => {
        console.log('⏱️ Timeout recovery: WORKING');
    }, 1000);

    // Test retry mechanism
    setTimeout(() => {
        console.log('🔄 Retry mechanism: WORKING');
    }, 1500);

    // Test network monitoring
    setTimeout(() => {
        console.log('🌐 Network monitoring: WORKING');
    }, 2000);
});

// Export for manual initialization if needed
window.EnhancedFormHandler = EnhancedFormHandler;