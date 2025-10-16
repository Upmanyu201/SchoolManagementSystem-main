/**
 * Universal Export System JavaScript
 * Handles export functionality for all modules
 */

class ExportSystem {
    constructor() {
        this.initializeExportButtons();
    }

    initializeExportButtons() {
        // Add event listeners to export buttons
        document.addEventListener('DOMContentLoaded', () => {
            const exportButtons = document.querySelectorAll('[data-export]');
            exportButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    const format = button.getAttribute('data-export');
                    this.handleExport(format);
                });
            });
        });
    }

    handleExport(format) {
        // Show loading state
        this.showExportLoading(format);
        
        // Get current URL and add export parameter
        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.set('export', format);
        
        // Create hidden form for download
        const form = document.createElement('form');
        form.method = 'GET';
        form.action = currentUrl.toString();
        form.style.display = 'none';
        
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
        
        // Hide loading state after delay
        setTimeout(() => {
            this.hideExportLoading(format);
        }, 2000);
    }

    showExportLoading(format) {
        const button = document.querySelector(`[data-export="${format}"]`);
        if (button) {
            const originalText = button.innerHTML;
            button.setAttribute('data-original-text', originalText);
            button.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i>Exporting...`;
            button.disabled = true;
        }
    }

    hideExportLoading(format) {
        const button = document.querySelector(`[data-export="${format}"]`);
        if (button) {
            const originalText = button.getAttribute('data-original-text');
            button.innerHTML = originalText;
            button.disabled = false;
        }
    }

    // Utility method to add export buttons to any table
    static addExportButtons(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const exportHtml = `
            <div class="export-buttons mb-4">
                <div class="btn-group" role="group">
                    <button type="button" class="btn btn-success" data-export="excel">
                        <i class="fas fa-file-excel mr-2"></i>Excel (.xlsx)
                    </button>
                    <button type="button" class="btn btn-info" data-export="csv">
                        <i class="fas fa-file-csv mr-2"></i>CSV
                    </button>
                    <button type="button" class="btn btn-danger" data-export="pdf">
                        <i class="fas fa-file-pdf mr-2"></i>PDF
                    </button>
                </div>
            </div>
        `;

        container.insertAdjacentHTML('afterbegin', exportHtml);
    }
}

// Initialize export system
const exportSystem = new ExportSystem();

// Export for global use
window.ExportSystem = ExportSystem;