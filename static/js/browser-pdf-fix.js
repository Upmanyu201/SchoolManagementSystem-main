/**
 * 🔧 Browser PDF Export Fix
 * Prevents IDM/CDM interference and empty file downloads
 */

class BrowserPDFExportFix {
    constructor() {
        this.isExporting = false;
        this.exportTimeout = null;
        this.init();
    }
    
    init() {
        // Detect download manager interference
        this.detectDownloadManager();
        
        // Override export functions
        this.overrideExportFunctions();
        
        // Add browser-specific fixes
        this.addBrowserFixes();
    }
    
    detectDownloadManager() {
        // Check for IDM/CDM presence
        const hasIDM = window.external && window.external.AddFavorite;
        const hasDownloadManager = navigator.plugins && 
            Array.from(navigator.plugins).some(p => 
                p.name.toLowerCase().includes('download') || 
                p.name.toLowerCase().includes('idm')
            );
        
        if (hasIDM || hasDownloadManager) {
            console.warn('🚨 Download manager detected - applying fixes');
            this.applyDownloadManagerFix();
        }
    }
    
    applyDownloadManagerFix() {
        // Method 1: Use blob download instead of direct URL
        window.exportPDFSafe = async (url) => {
            if (this.isExporting) return;
            this.isExporting = true;
            
            try {
                const response = await fetch(url, {
                    method: 'GET',
                    credentials: 'same-origin',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                
                const blob = await response.blob();
                if (blob.size === 0) throw new Error('Empty PDF received');
                
                // Create download using blob URL
                const blobUrl = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = blobUrl;
                link.download = `export_${Date.now()}.pdf`;
                link.style.display = 'none';
                
                document.body.appendChild(link);
                link.click();
                
                // Cleanup
                setTimeout(() => {
                    document.body.removeChild(link);
                    URL.revokeObjectURL(blobUrl);
                    this.isExporting = false;
                }, 1000);
                
            } catch (error) {
                console.error('PDF export failed:', error);
                this.isExporting = false;
                alert('PDF export failed. Please try again.');
            }
        };
    }
    
    overrideExportFunctions() {
        // Override any existing export functions
        const originalOpen = window.open;
        window.open = function(url, ...args) {
            if (url && url.includes('export') && url.includes('pdf')) {
                console.log('🔄 Redirecting PDF export through safe method');
                window.exportPDFSafe(url);
                return null;
            }
            return originalOpen.call(this, url, ...args);
        };
    }
    
    addBrowserFixes() {
        // Chrome-specific fixes
        if (navigator.userAgent.includes('Chrome')) {
            this.addChromeFixes();
        }
        
        // Firefox-specific fixes
        if (navigator.userAgent.includes('Firefox')) {
            this.addFirefoxFixes();
        }
        
        // Edge-specific fixes
        if (navigator.userAgent.includes('Edge')) {
            this.addEdgeFixes();
        }
    }
    
    addChromeFixes() {
        console.log('🔧 Applying Chrome-specific PDF fixes');
        // Prevent multiple simultaneous downloads
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href*="pdf"]');
            if (link && this.isExporting) {
                e.preventDefault();
                console.log('🚫 Blocked duplicate PDF export');
            }
        });
    }
    
    addFirefoxFixes() {
        console.log('🔧 Applying Firefox-specific PDF fixes');
        // Firefox handles downloads differently
    }
    
    addEdgeFixes() {
        console.log('🔧 Applying Edge-specific PDF fixes');
        // Edge similar to Chrome
        this.addChromeFixes();
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new BrowserPDFExportFix();
    });
} else {
    new BrowserPDFExportFix();
}
