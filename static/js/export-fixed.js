/**
 * 🔧 FIXED Export Manager - Prevents Duplicate Downloads
 * Addresses issues from chat.md analysis
 */

class FixedExportManager {
    constructor() {
        this.isExporting = false;
        this.exportCooldown = 2000; // 2 second cooldown
        this.lastExportTime = 0;
        this.initializeButtons();
    }

    initializeButtons() {
        document.addEventListener('DOMContentLoaded', () => {
            // ✅ FIXED: Single event listener to prevent double requests
            const exportButtons = document.querySelectorAll('[data-export]');
            exportButtons.forEach(button => {
                // Remove any existing listeners
                button.replaceWith(button.cloneNode(true));
            });
            
            // Add single click handler
            document.addEventListener('click', (e) => {
                const button = e.target.closest('[data-export]');
                if (button) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const format = button.getAttribute('data-export');
                    this.handleExport(format, button);
                }
            });
        });
    }

    handleExport(format, button) {
        // ✅ FIXED: Prevent duplicate exports with cooldown
        const now = Date.now();
        if (this.isExporting || (now - this.lastExportTime) < this.exportCooldown) {
            console.log('Export blocked - already in progress or cooldown active');
            return;
        }

        this.isExporting = true;
        this.lastExportTime = now;
        
        // Show loading state
        this.showLoading(button);
        
        // ✅ FIXED: Use direct window.location instead of fetch + window.open
        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.set('export', format);
        
        // ✅ FIXED: Single request method - no double downloads
        window.location.href = currentUrl.toString();
        
        // Reset state after delay
        setTimeout(() => {
            this.isExporting = false;
            this.hideLoading(button);
        }, 3000);
    }

    showLoading(button) {
        if (button) {
            const originalText = button.innerHTML;
            button.setAttribute('data-original-text', originalText);
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Exporting...';
            button.disabled = true;
        }
    }

    hideLoading(button) {
        if (button) {
            const originalText = button.getAttribute('data-original-text');
            if (originalText) {
                button.innerHTML = originalText;
            }
            button.disabled = false;
        }
    }
}

// ✅ FIXED: Initialize only once
if (!window.fixedExportManager) {
    window.fixedExportManager = new FixedExportManager();
}
