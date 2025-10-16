// Fee Report Export Functions
function exportFeeReport(format) {
    const button = event.target.closest('button');
    const originalText = button.innerHTML;
    
    // Show loading state
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Exporting...';
    button.disabled = true;
    
    try {
        if (format === 'excel') {
            // Special handling for Excel files
            exportExcelFile();
        } else {
            // Standard download for CSV and PDF
            const downloadUrl = `/backup/api/export/fees_report/${format}/`;
            
            // Create temporary link for download
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `fees_report_${new Date().toISOString().split('T')[0]}.${format}`;
            link.style.display = 'none';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        
        // Show success message
        showNotification(`Fee report export started in ${format.toUpperCase()} format`, 'success');
        
    } catch (error) {
        console.error('Export failed:', error);
        showNotification('Export failed. Please try again.', 'error');
    }
    
    // Reset button after delay
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 2000);
}

// Special Excel export function
async function exportExcelFile() {
    try {
        const response = await fetch('/backup/api/export/fees_report/excel/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Get the blob data
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `student_fee_report_${new Date().toISOString().split('T')[0]}.xlsx`;
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up
        window.URL.revokeObjectURL(url);
        
        console.log('✅ Excel download completed successfully');
        
    } catch (error) {
        console.error('❌ Excel export failed:', error);
        showNotification('Excel export failed. Please try again.', 'error');
        throw error;
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showNotification(message, type = 'info') {
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