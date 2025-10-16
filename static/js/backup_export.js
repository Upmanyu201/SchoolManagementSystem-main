// Backup Export System Functions
function exportSystem() {
    return {
        modules: [],
        exporting: false,
        
        async init() {
            await this.loadModules();
        },
        
        async loadModules() {
            try {
                const response = await fetch('/backup/api/export/modules/');
                const data = await response.json();
                this.modules = data.modules || [];
            } catch (error) {
                console.error('Failed to load export modules:', error);
            }
        },
        
        async exportData(moduleKey, format) {
            if (this.exporting) return;
            
            this.exporting = true;
            
            try {
                // Use correct API URL structure
                const url = `/backup/api/export/${moduleKey}/${format}/`;
                const link = document.createElement('a');
                link.href = url;
                link.download = `${moduleKey}_export_${new Date().toISOString().split('T')[0]}.${format}`;
                link.style.display = 'none';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                // Show success message
                this.showNotification(`${format.toUpperCase()} export started for ${moduleKey}`, 'success');
                
            } catch (error) {
                console.error('Export failed:', error);
                this.showNotification('Export failed. Please try again.', 'error');
            } finally {
                setTimeout(() => {
                    this.exporting = false;
                }, 2000);
            }
        },
        
        showNotification(message, type) {
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg ${
                type === 'success' ? 'bg-green-500' : 
                type === 'error' ? 'bg-red-500' : 'bg-blue-500'
            } text-white`;
            notification.innerHTML = `
                <div class="flex items-center">
                    <i class="fas ${
                        type === 'success' ? 'fa-check-circle' : 
                        type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'
                    } mr-2"></i>
                    <span>${message}</span>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.opacity = '0';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }
    }
}