// Export function fix for CSV and Excel downloads
function exportData(moduleKey, format) {
    const url = `/backup/api/export/${moduleKey}/${format}/`;
    
    // Create temporary link for download
    const link = document.createElement('a');
    link.href = url;
    link.download = `${moduleKey}_export.${format}`;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log(`📥 Downloading ${format.toUpperCase()} for ${moduleKey}`);
}

// Alternative method if above doesn't work
function exportDataFetch(moduleKey, format) {
    fetch(`/backup/api/export/${moduleKey}/${format}/`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `${moduleKey}_export.${format}`;
            link.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => console.error('Export failed:', error));
}