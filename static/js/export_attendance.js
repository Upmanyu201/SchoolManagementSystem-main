// Export functionality for attendance module
function exportAttendance(format = 'csv') {
    const selectedDate = document.getElementById('reportDate').value;
    
    if (!selectedDate) {
        alert('Please select a date first');
        return;
    }
    
    const exportUrl = `/backup/export/attendance/?format=${format}&date=${selectedDate}`;
    
    // Show loading state
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Exporting...';
    button.disabled = true;
    
    // Create download link
    const link = document.createElement('a');
    link.href = exportUrl;
    link.download = `attendance_${selectedDate}.${format}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Reset button after delay
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 2000);
}

// Add export button to attendance report
document.addEventListener('DOMContentLoaded', function() {
    const exportContainer = document.getElementById('exportContainer');
    if (exportContainer) {
        // Add export buttons for different formats
        exportContainer.innerHTML = `
            <div class="flex flex-col gap-3">
                <button onclick="exportAttendance('csv')" 
                        class="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-6 py-4 rounded-full shadow-2xl transition-all duration-300 transform hover:scale-110">
                    <i class="fas fa-download mr-2"></i>Export CSV
                </button>
                <div class="flex gap-2">
                    <button onclick="exportAttendance('excel')" 
                            class="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-4 py-2 rounded-lg shadow-lg transition-all duration-300 transform hover:scale-105">
                        <i class="fas fa-file-excel mr-1"></i>Excel
                    </button>
                    <button onclick="exportAttendance('pdf')" 
                            class="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white px-4 py-2 rounded-lg shadow-lg transition-all duration-300 transform hover:scale-105">
                        <i class="fas fa-file-pdf mr-1"></i>PDF
                    </button>
                </div>
            </div>
        `;
    }
});