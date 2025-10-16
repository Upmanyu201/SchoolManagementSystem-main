/**
 * 📊 Export API Tracker
 * Comprehensive logging for export requests and responses
 */

class ExportTracker {
    constructor() {
        this.exportAttempts = new Map();
        this.sessionId = this.generateSessionId();
        this.init();
    }
    
    generateSessionId() {
        return 'export_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    init() {
        console.log(`🔍 Export Tracker initialized - Session: ${this.sessionId}`);
        this.interceptFetch();
        this.interceptWindowOpen();
        this.trackPageUnload();
    }
    
    log(level, message, data = {}) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            session: this.sessionId,
            level,
            message,
            ...data
        };
        
        console.log(`[${level.toUpperCase()}] ${timestamp} - ${message}`, data);
        
        // Store in sessionStorage for debugging
        try {
            const logs = JSON.parse(sessionStorage.getItem('exportLogs') || '[]');
            logs.push(logEntry);
            // Keep only last 50 logs
            if (logs.length > 50) logs.shift();
            sessionStorage.setItem('exportLogs', JSON.stringify(logs));
        } catch (e) {
            console.warn('Failed to store export log:', e);
        }
    }
    
    trackExportAttempt(url, method = 'GET') {
        const attemptId = `${method}_${url}_${Date.now()}`;
        const attempt = {
            id: attemptId,
            url,
            method,
            startTime: Date.now(),
            userAgent: navigator.userAgent,
            referrer: document.referrer,
            status: 'started'
        };
        
        this.exportAttempts.set(attemptId, attempt);
        
        this.log('info', '🚀 Export attempt started', {
            attemptId,
            url,
            method,
            userAgent: navigator.userAgent.substring(0, 50) + '...'
        });
        
        return attemptId;
    }
    
    trackExportResponse(attemptId, response, error = null) {
        const attempt = this.exportAttempts.get(attemptId);
        if (!attempt) {
            this.log('warn', '⚠️ Unknown export attempt response', { attemptId });
            return;
        }
        
        const duration = Date.now() - attempt.startTime;
        attempt.endTime = Date.now();
        attempt.duration = duration;
        attempt.status = error ? 'error' : 'success';
        
        if (response) {
            attempt.responseSize = response.size || 0;
            attempt.responseType = response.type || 'unknown';
            attempt.responseStatus = response.status || 0;
        }
        
        if (error) {
            attempt.error = error.message || error.toString();
        }
        
        this.log(error ? 'error' : 'info', 
            error ? '❌ Export failed' : '✅ Export completed', {
            attemptId,
            duration: `${duration}ms`,
            responseSize: attempt.responseSize,
            responseType: attempt.responseType,
            error: attempt.error
        });
        
        // Check for potential issues
        this.analyzeAttempt(attempt);
    }
    
    analyzeAttempt(attempt) {
        const issues = [];
        
        // Check for slow responses
        if (attempt.duration > 5000) {
            issues.push('Slow response (>5s)');
        }
        
        // Check for empty responses
        if (attempt.responseSize === 0) {
            issues.push('Empty response (0 bytes)');
        }
        
        // Check for duplicate attempts
        const recentAttempts = Array.from(this.exportAttempts.values())
            .filter(a => a.url === attempt.url && 
                         Math.abs(a.startTime - attempt.startTime) < 2000);
        
        if (recentAttempts.length > 1) {
            issues.push(`Duplicate attempts (${recentAttempts.length})`);
        }
        
        if (issues.length > 0) {
            this.log('warn', '⚠️ Export issues detected', {
                attemptId: attempt.id,
                issues,
                url: attempt.url
            });
        }
    }
    
    interceptFetch() {
        const originalFetch = window.fetch;
        const tracker = this;
        
        window.fetch = async function(url, options = {}) {
            // Only track export-related requests
            if (typeof url === 'string' && url.includes('export')) {
                const attemptId = tracker.trackExportAttempt(url, options.method || 'GET');
                
                try {
                    const response = await originalFetch(url, options);
                    
                    // Clone response to read size
                    const clonedResponse = response.clone();
                    const blob = await clonedResponse.blob();
                    
                    tracker.trackExportResponse(attemptId, {
                        status: response.status,
                        size: blob.size,
                        type: blob.type
                    });
                    
                    return response;
                } catch (error) {
                    tracker.trackExportResponse(attemptId, null, error);
                    throw error;
                }
            }
            
            return originalFetch(url, options);
        };
    }
    
    interceptWindowOpen() {
        const originalOpen = window.open;
        const tracker = this;
        
        window.open = function(url, ...args) {
            if (url && url.includes('export')) {
                const attemptId = tracker.trackExportAttempt(url, 'WINDOW_OPEN');
                
                // Track window open attempt
                setTimeout(() => {
                    tracker.trackExportResponse(attemptId, {
                        status: 200,
                        size: 'unknown',
                        type: 'window_open'
                    });
                }, 1000);
            }
            
            return originalOpen.call(this, url, ...args);
        };
    }
    
    trackPageUnload() {
        window.addEventListener('beforeunload', () => {
            const pendingAttempts = Array.from(this.exportAttempts.values())
                .filter(a => a.status === 'started');
            
            if (pendingAttempts.length > 0) {
                this.log('warn', '⚠️ Page unloading with pending exports', {
                    pendingCount: pendingAttempts.length,
                    attempts: pendingAttempts.map(a => a.url)
                });
            }
        });
    }
    
    // Public method to get export statistics
    getStats() {
        const attempts = Array.from(this.exportAttempts.values());
        const stats = {
            total: attempts.length,
            successful: attempts.filter(a => a.status === 'success').length,
            failed: attempts.filter(a => a.status === 'error').length,
            pending: attempts.filter(a => a.status === 'started').length,
            avgDuration: 0,
            duplicates: 0
        };
        
        const completedAttempts = attempts.filter(a => a.duration);
        if (completedAttempts.length > 0) {
            stats.avgDuration = completedAttempts.reduce((sum, a) => sum + a.duration, 0) / completedAttempts.length;
        }
        
        // Count duplicates (same URL within 2 seconds)
        const urlGroups = {};
        attempts.forEach(a => {
            const key = `${a.url}_${Math.floor(a.startTime / 2000)}`;
            urlGroups[key] = (urlGroups[key] || 0) + 1;
        });
        stats.duplicates = Object.values(urlGroups).filter(count => count > 1).length;
        
        return stats;
    }
    
    // Public method to get recent logs
    getLogs() {
        try {
            return JSON.parse(sessionStorage.getItem('exportLogs') || '[]');
        } catch (e) {
            return [];
        }
    }
    
    // Public method to clear logs
    clearLogs() {
        sessionStorage.removeItem('exportLogs');
        this.exportAttempts.clear();
        this.log('info', '🧹 Export logs cleared');
    }
}

// Initialize tracker when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.exportTracker = new ExportTracker();
    });
} else {
    window.exportTracker = new ExportTracker();
}

// Add global functions for debugging
window.getExportStats = () => window.exportTracker?.getStats();
window.getExportLogs = () => window.exportTracker?.getLogs();
window.clearExportLogs = () => window.exportTracker?.clearLogs();

// Console helper
console.log('📊 Export Tracker loaded. Use getExportStats(), getExportLogs(), clearExportLogs() for debugging.');