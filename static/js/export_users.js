// Export functionality for users module
function exportUsers(format = 'csv') {
    const exportUrl = `/backup/export/users/?format=${format}`;
    
    // Show loading state
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Exporting...';
    button.disabled = true;
    
    // Create download link
    const link = document.createElement('a');
    link.href = exportUrl;
    link.download = `users_export.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Reset button after delay
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 2000);
}

// Add export functionality to user management page
document.addEventListener('DOMContentLoaded', function() {
    // Add export dropdown to header
    const headerActions = document.querySelector('.bg-gradient-to-r.from-blue-600 .flex.gap-3');
    if (headerActions) {
        const exportButton = document.createElement('div');
        exportButton.className = 'relative';
        exportButton.innerHTML = `
            <button onclick="toggleExportDropdown()" 
                    class="btn-modern bg-emerald-500 hover:bg-emerald-600 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg flex items-center justify-center gap-2">
                <i class="fas fa-download"></i>
                <span class="hidden sm:inline">Export Users</span>
                <span class="sm:hidden">Export</span>
                <i class="fas fa-chevron-down ml-1"></i>
            </button>
            <div id="exportDropdown" class="hidden absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-xl border border-gray-200 z-50">
                <button onclick="exportUsers('csv')" class="w-full text-left px-4 py-3 hover:bg-gray-50 flex items-center gap-2">
                    <i class="fas fa-file-csv text-green-500"></i>Export as CSV
                </button>
                <button onclick="exportUsers('excel')" class="w-full text-left px-4 py-3 hover:bg-gray-50 flex items-center gap-2">
                    <i class="fas fa-file-excel text-blue-500"></i>Export as Excel
                </button>
                <button onclick="exportUsers('pdf')" class="w-full text-left px-4 py-3 hover:bg-gray-50 flex items-center gap-2">
                    <i class="fas fa-file-pdf text-red-500"></i>Export as PDF
                </button>
            </div>
        `;
        headerActions.appendChild(exportButton);
    }
});

function toggleExportDropdown() {
    const dropdown = document.getElementById('exportDropdown');
    dropdown.classList.toggle('hidden');
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('#exportDropdown') && !event.target.closest('button[onclick="toggleExportDropdown()"]')) {
            dropdown.classList.add('hidden');
        }
    });
}