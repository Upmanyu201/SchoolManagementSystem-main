/**
 * Professional Attendance Reports Handler
 * Handles attendance report generation, export, and UI interactions
 */

class ProfessionalAttendanceHandler {
    constructor() {
        this.currentReportData = null;
        this.selectedDate = null;
        this.init();
    }

    init() {
        console.log('✅ Professional Attendance Handler initialized');
        this.setupEventListeners();
        this.setupAnimations();
        this.setDefaultDate();
    }

    setupEventListeners() {
        // Date input handler
        const dateInput = document.getElementById('reportDate');
        if (dateInput) {
            dateInput.addEventListener('change', (e) => {
                this.selectedDate = e.target.value;
                this.updateSelectedDateDisplay();
                this.showMessage('Date selected. Click "Generate Report" to view attendance data.', 'info');
            });
        }

        // Generate report button
        const generateBtn = document.getElementById('generateReport');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => {
                this.generateReport();
            });
        }

        // Export button
        const exportBtn = document.getElementById('exportReport');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportReport();
            });
        }
    }

    setupAnimations() {
        // Animate cards on load
        const cards = document.querySelectorAll('.transform, .card-hover');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.6s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });

        // Add hover effects to interactive elements
        const interactiveElements = document.querySelectorAll('button, a, .btn');
        interactiveElements.forEach(element => {
            element.addEventListener('mouseenter', function() {
                if (!this.disabled) {
                    this.style.transform = 'scale(1.05)';
                }
            });
            
            element.addEventListener('mouseleave', function() {
                this.style.transform = 'scale(1)';
            });
        });
    }

    setDefaultDate() {
        const today = new Date();
        const dateString = today.toISOString().split('T')[0];
        const dateInput = document.getElementById('reportDate');
        if (dateInput) {
            dateInput.value = dateString;
            this.selectedDate = dateString;
            this.updateSelectedDateDisplay();
        }
    }

    updateSelectedDateDisplay() {
        const displayElement = document.getElementById('selectedDateDisplay');
        if (displayElement && this.selectedDate) {
            const date = new Date(this.selectedDate);
            const formattedDate = date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            displayElement.textContent = formattedDate;
        }
    }

    async generateReport() {
        if (!this.selectedDate) {
            this.showMessage('Please select a date first.', 'error');
            return;
        }

        const generateBtn = document.getElementById('generateReport');
        const originalText = generateBtn.innerHTML;
        
        try {
            // Show loading state
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Generating Report...';
            generateBtn.disabled = true;

            // Fetch report data
            const response = await fetch(`/attendance/report/?date=${this.selectedDate}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (data.error) {
                throw new Error(data.error);
            }

            this.currentReportData = data.report || [];
            this.displayReport();
            this.showMessage('Report generated successfully!', 'success');

        } catch (error) {
            console.error('❌ Report generation error:', error);
            let errorMessage = 'Error generating report';
            if (error.message) {
                errorMessage = error.message.includes('HTTP') ? 'Server error. Please try again.' : error.message;
            }
            this.showMessage(errorMessage, 'error');
        } finally {
            generateBtn.innerHTML = originalText;
            generateBtn.disabled = false;
        }
    }

    displayReport() {
        const reportTable = document.getElementById('reportTable');
        const emptyState = document.getElementById('emptyState');
        const summaryCards = document.getElementById('summaryCards');
        const reportData = document.getElementById('reportData');
        const exportBtn = document.getElementById('exportReport');

        if (!this.currentReportData || this.currentReportData.length === 0) {
            if (reportTable) reportTable.classList.add('hidden');
            if (summaryCards) summaryCards.classList.add('hidden');
            if (emptyState) emptyState.classList.remove('hidden');
            if (exportBtn) exportBtn.disabled = true;
            const exportContainer = document.getElementById('exportContainer');
            if (exportContainer) exportContainer.classList.add('hidden');
            return;
        }

        // Calculate totals
        let totalClasses = this.currentReportData.length;
        let totalStudents = 0;
        let totalPresent = 0;
        let totalAbsent = 0;

        // Clear existing data
        if (!reportData) {
            console.error('❌ reportData element not found');
            return;
        }
        reportData.innerHTML = '';

        // Generate table rows
        this.currentReportData.forEach((item, index) => {
            totalStudents += item.total_students;
            totalPresent += item.present;
            totalAbsent += item.absent;

            const attendanceRate = item.total_students > 0 
                ? ((item.present / item.total_students) * 100).toFixed(1)
                : 0;

            const progressClass = this.getProgressClass(attendanceRate);
            
            const row = document.createElement('tr');
            row.className = 'hover:bg-gradient-to-r hover:from-purple-50 hover:to-indigo-50 transition-all duration-300 transform hover:scale-[1.01]';
            row.style.opacity = '0';
            row.style.transform = 'translateX(-20px)';

            row.innerHTML = `
                <td class="px-6 py-4">
                    <div class="flex items-center">
                        <div class="w-10 h-10 bg-gradient-to-r from-purple-500 to-indigo-600 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-school text-white"></i>
                        </div>
                        <div>
                            <div class="font-bold text-gray-900">🏫 ${item.class_name}</div>
                            <div class="text-sm text-gray-500">Class Details</div>
                        </div>
                    </div>
                </td>
                <td class="px-4 py-4 text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gradient-to-r from-blue-100 to-cyan-100 text-blue-800 border border-blue-200">
                        👥 ${item.total_students}
                    </span>
                </td>
                <td class="px-4 py-4 text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gradient-to-r from-green-100 to-emerald-100 text-green-800 border border-green-200">
                        ✅ ${item.present}
                    </span>
                </td>
                <td class="px-4 py-4 text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gradient-to-r from-red-100 to-pink-100 text-red-800 border border-red-200">
                        ❌ ${item.absent}
                    </span>
                </td>
                <td class="px-4 py-4 text-center">
                    <div class="flex flex-col items-center gap-2">
                        <div class="w-20 progress-bar">
                            <div class="progress-fill ${progressClass}" style="width: ${attendanceRate}%"></div>
                        </div>
                        <span class="text-sm font-bold ${this.getTextClass(attendanceRate)}">${attendanceRate}%</span>
                    </div>
                </td>
                <td class="px-4 py-4 text-center">
                    <button onclick="professionalAttendance.viewStudentDetails('${item.class_name}', '${this.selectedDate}')" 
                            class="inline-flex items-center bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white px-4 py-2 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg">
                        <i class="fas fa-eye mr-2"></i>View Details
                    </button>
                </td>
            `;

            reportData.appendChild(row);

            // Animate row appearance
            setTimeout(() => {
                row.style.transition = 'all 0.4s ease';
                row.style.opacity = '1';
                row.style.transform = 'translateX(0)';
            }, index * 50);
        });

        // Update summary cards
        this.updateSummaryCards(totalClasses, totalStudents, totalPresent, totalAbsent);

        // Show report and hide empty state
        if (emptyState) emptyState.classList.add('hidden');
        if (reportTable) reportTable.classList.remove('hidden');
        if (summaryCards) summaryCards.classList.remove('hidden');
        if (exportBtn) exportBtn.disabled = false;
        const exportContainer = document.getElementById('exportContainer');
        if (exportContainer) exportContainer.classList.remove('hidden');
    }

    updateSummaryCards(totalClasses, totalStudents, totalPresent, totalAbsent) {
        document.getElementById('totalClasses').textContent = totalClasses;
        document.getElementById('totalStudents').textContent = totalStudents;
        document.getElementById('totalPresent').textContent = totalPresent;
        document.getElementById('totalAbsent').textContent = totalAbsent;

        // Animate summary cards
        const cards = document.querySelectorAll('#summaryCards .bg-gradient-to-br');
        cards.forEach((card, index) => {
            card.style.transform = 'scale(0.8)';
            card.style.opacity = '0.5';
            
            setTimeout(() => {
                card.style.transition = 'all 0.5s ease';
                card.style.transform = 'scale(1)';
                card.style.opacity = '1';
            }, index * 100);
        });
    }

    async viewStudentDetails(className, date) {
        try {
            this.showLoader('Loading student details...');

            const response = await fetch(`/attendance/report/?class_name=${encodeURIComponent(className)}&date=${date}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            this.displayStudentDetails(className, date, data.students || []);

        } catch (error) {
            console.error('❌ Error loading student details:', error);
            this.showMessage(`Error loading details: ${error.message}`, 'error');
        } finally {
            this.hideLoader();
        }
    }

    displayStudentDetails(className, date, students) {
        const modal = document.getElementById('studentDetailsModal');
        const modalTitle = document.getElementById('modalTitle');
        const content = document.getElementById('studentDetailsContent');

        modalTitle.innerHTML = `<i class="fas fa-users mr-2"></i>🏫 ${className} - ${this.formatDate(date)}`;

        let detailsHtml = '';

        if (students.length > 0) {
            const presentStudents = students.filter(s => s.status === 'Present');
            const absentStudents = students.filter(s => s.status === 'Absent');
            const noRecordStudents = students.filter(s => s.status === 'No Record');

            detailsHtml = `
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <!-- Present Students -->
                    <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border border-green-200">
                        <h4 class="text-lg font-bold text-green-800 mb-4 flex items-center">
                            <i class="fas fa-check-circle mr-2"></i>✅ Present (${presentStudents.length})
                        </h4>
                        <div class="space-y-2 max-h-64 overflow-y-auto">
                            ${presentStudents.map(student => `
                                <div class="flex items-center p-3 bg-white rounded-lg shadow-sm border border-green-100">
                                    <div class="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center mr-3">
                                        <i class="fas fa-user text-white text-sm"></i>
                                    </div>
                                    <span class="font-medium text-gray-800">${student.name}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Absent Students -->
                    <div class="bg-gradient-to-br from-red-50 to-pink-50 rounded-2xl p-6 border border-red-200">
                        <h4 class="text-lg font-bold text-red-800 mb-4 flex items-center">
                            <i class="fas fa-times-circle mr-2"></i>❌ Absent (${absentStudents.length})
                        </h4>
                        <div class="space-y-2 max-h-64 overflow-y-auto">
                            ${absentStudents.map(student => `
                                <div class="flex items-center p-3 bg-white rounded-lg shadow-sm border border-red-100">
                                    <div class="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center mr-3">
                                        <i class="fas fa-user text-white text-sm"></i>
                                    </div>
                                    <span class="font-medium text-gray-800">${student.name}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- No Record Students -->
                    <div class="bg-gradient-to-br from-gray-50 to-slate-50 rounded-2xl p-6 border border-gray-200">
                        <h4 class="text-lg font-bold text-gray-800 mb-4 flex items-center">
                            <i class="fas fa-question-circle mr-2"></i>❓ No Record (${noRecordStudents.length})
                        </h4>
                        <div class="space-y-2 max-h-64 overflow-y-auto">
                            ${noRecordStudents.map(student => `
                                <div class="flex items-center p-3 bg-white rounded-lg shadow-sm border border-gray-100">
                                    <div class="w-8 h-8 bg-gray-500 rounded-full flex items-center justify-center mr-3">
                                        <i class="fas fa-user text-white text-sm"></i>
                                    </div>
                                    <span class="font-medium text-gray-800">${student.name}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- Summary Stats -->
                <div class="mt-6 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-6 border border-indigo-200">
                    <h4 class="text-lg font-bold text-indigo-800 mb-4 flex items-center">
                        <i class="fas fa-chart-pie mr-2"></i>📊 Class Summary
                    </h4>
                    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-blue-600">${students.length}</div>
                            <div class="text-sm text-gray-600">Total Students</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-green-600">${presentStudents.length}</div>
                            <div class="text-sm text-gray-600">Present</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-red-600">${absentStudents.length}</div>
                            <div class="text-sm text-gray-600">Absent</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-indigo-600">
                                ${students.length > 0 ? ((presentStudents.length / students.length) * 100).toFixed(1) : 0}%
                            </div>
                            <div class="text-sm text-gray-600">Attendance Rate</div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            detailsHtml = `
                <div class="text-center py-12">
                    <i class="fas fa-users text-6xl text-gray-300 mb-4"></i>
                    <h4 class="text-xl font-bold text-gray-500 mb-2">No Student Data Found</h4>
                    <p class="text-gray-400">No attendance records found for this class on the selected date.</p>
                </div>
            `;
        }

        content.innerHTML = detailsHtml;
        modal.classList.remove('hidden');

        // Animate modal appearance
        setTimeout(() => {
            modal.querySelector('.bg-white').style.transform = 'scale(1)';
            modal.querySelector('.bg-white').style.opacity = '1';
        }, 10);
    }

    closeStudentModal() {
        const modal = document.getElementById('studentDetailsModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    async exportReport() {
        if (!this.currentReportData || this.currentReportData.length === 0) {
            this.showMessage('No data to export. Please generate a report first.', 'error');
            return;
        }

        try {
            this.showExportLoader();
            
            // Create CSV data
            const csvData = this.generateCSVData();
            const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
            
            // Create download link
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `attendance_report_${this.selectedDate}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showMessage('Report exported successfully!', 'success');
            
        } catch (error) {
            console.error('❌ Export error:', error);
            this.showMessage(`Export failed: ${error.message}`, 'error');
        } finally {
            this.hideExportLoader();
        }
    }

    generateCSVData() {
        const headers = ['Class Name', 'Total Students', 'Present', 'Absent', 'Attendance Rate (%)'];
        const rows = [headers];

        this.currentReportData.forEach(item => {
            const attendanceRate = item.total_students > 0 
                ? ((item.present / item.total_students) * 100).toFixed(1)
                : 0;
            
            rows.push([
                item.class_name,
                item.total_students,
                item.present,
                item.absent,
                attendanceRate
            ]);
        });

        // Add summary row
        const totalStudents = this.currentReportData.reduce((sum, item) => sum + item.total_students, 0);
        const totalPresent = this.currentReportData.reduce((sum, item) => sum + item.present, 0);
        const totalAbsent = this.currentReportData.reduce((sum, item) => sum + item.absent, 0);
        const overallRate = totalStudents > 0 ? ((totalPresent / totalStudents) * 100).toFixed(1) : 0;

        rows.push(['TOTAL', totalStudents, totalPresent, totalAbsent, overallRate]);

        return rows.map(row => row.map(field => `"${field}"`).join(',')).join('\n');
    }

    getProgressClass(rate) {
        if (rate >= 90) return 'progress-excellent';
        if (rate >= 75) return 'progress-good';
        if (rate >= 60) return 'progress-average';
        return 'progress-poor';
    }

    getTextClass(rate) {
        if (rate >= 90) return 'text-green-600';
        if (rate >= 75) return 'text-blue-600';
        if (rate >= 60) return 'text-yellow-600';
        return 'text-red-600';
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    showLoader(message = 'Processing...') {
        // Implementation similar to professional reports
    }

    hideLoader() {
        // Implementation similar to professional reports
    }

    showExportLoader() {
        const loader = document.getElementById('export-loader');
        if (loader) {
            loader.classList.remove('hidden');
        }
    }

    hideExportLoader() {
        const loader = document.getElementById('export-loader');
        if (loader) {
            loader.classList.add('hidden');
        }
    }

    showMessage(message, type = 'info') {
        // Create or update message element
        let messageEl = document.getElementById('attendance-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'attendance-message';
            messageEl.className = 'fixed top-4 right-4 z-50 p-4 rounded-xl shadow-lg transition-all duration-300';
            document.body.appendChild(messageEl);
        }

        // Set message content and style
        const colors = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            info: 'bg-blue-500 text-white',
            warning: 'bg-yellow-500 text-black'
        };

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            info: 'fa-info-circle',
            warning: 'fa-exclamation-triangle'
        };

        messageEl.className = `fixed right-4 z-50 p-4 rounded-xl shadow-lg transition-all duration-300 ${colors[type] || colors.info}`;
        messageEl.style.top = 'calc(var(--topbar-height) + 1rem)';
        messageEl.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${icons[type] || icons.info} mr-2"></i>
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

// Quick date selection functions
function setQuickDate(type) {
    const dateInput = document.getElementById('reportDate');
    if (!dateInput) return;
    
    const today = new Date();
    let targetDate;

    switch (type) {
        case 'today':
            targetDate = today;
            break;
        case 'yesterday':
            targetDate = new Date(today.getTime() - 24 * 60 * 60 * 1000);
            break;
        default:
            targetDate = today;
    }

    const dateString = targetDate.toISOString().split('T')[0];
    dateInput.value = dateString;
    
    // Trigger change event
    const changeEvent = new Event('change', { bubbles: true });
    dateInput.dispatchEvent(changeEvent);
    
    if (window.professionalAttendance) {
        window.professionalAttendance.selectedDate = dateString;
        window.professionalAttendance.updateSelectedDateDisplay();
        window.professionalAttendance.showMessage(`Date set to ${type}`, 'success');
    }
}

// Print function
function printReport() {
    window.print();
}

// Close modal function
function closeStudentModal() {
    if (window.professionalAttendance) {
        window.professionalAttendance.closeStudentModal();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Professional Attendance Handler...');
    
    try {
        window.professionalAttendance = new ProfessionalAttendanceHandler();
        console.log('✅ Professional Attendance Handler loaded successfully');
    } catch (error) {
        console.error('❌ Failed to initialize Professional Attendance Handler:', error);
    }
});

// Export for manual initialization if needed
window.ProfessionalAttendanceHandler = ProfessionalAttendanceHandler;