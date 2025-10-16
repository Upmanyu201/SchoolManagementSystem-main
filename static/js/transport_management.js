/**
 * Transport Management JavaScript
 * Handles inline editing, form validation, and UI interactions
 */

class TransportManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupFormValidation();
        this.setupSearch();
        this.autoHideMessages();
    }

    setupEventListeners() {
        // Assignment mode toggle
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-toggle-mode]')) {
                const mode = e.target.dataset.toggleMode;
                this.toggleAssignmentMode(mode);
            }
        });

        // Student selection checkboxes
        document.addEventListener('change', (e) => {
            if (e.target.matches('input[name="students"]')) {
                this.updateSelectedCount();
            }
        });

        // Form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('#assignmentForm')) {
                this.handleAssignmentSubmit(e);
            }
        });
    }

    setupFormValidation() {
        // Real-time validation for route form
        const routeNameField = document.querySelector('input[name="name"]');
        if (routeNameField) {
            routeNameField.addEventListener('input', this.validateRouteName.bind(this));
        }

        // Real-time validation for stoppage form
        const stoppageNameField = document.querySelector('input[name="name"]');
        if (stoppageNameField && stoppageNameField.closest('form').querySelector('[name="stoppage_submit"]')) {
            stoppageNameField.addEventListener('input', this.validateStoppageName.bind(this));
        }
    }

    setupSearch() {
        const searchInput = document.getElementById('studentSearch');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce(this.performSearch.bind(this), 300));
        }
    }

    // Assignment mode toggle
    toggleAssignmentMode(mode) {
        const singleMode = document.getElementById('singleStudentMode');
        const multipleMode = document.getElementById('multipleStudentsMode');
        const singleBtn = document.getElementById('singleModeBtn');
        const bulkBtn = document.getElementById('bulkModeBtn');
        const modeInput = document.getElementById('assignmentMode');
        const submitText = document.getElementById('submitBtnText');
        const studentSelect = document.getElementById('student_id');

        if (mode === 'single') {
            singleMode?.classList.remove('hidden');
            multipleMode?.classList.add('hidden');
            singleBtn?.classList.add('bg-gradient-to-r', 'from-blue-500', 'to-indigo-600', 'text-white');
            singleBtn?.classList.remove('text-gray-600', 'hover:text-gray-800');
            bulkBtn?.classList.remove('bg-gradient-to-r', 'from-green-500', 'to-emerald-600', 'text-white');
            bulkBtn?.classList.add('text-gray-600', 'hover:text-gray-800');
            
            if (modeInput) modeInput.value = 'single';
            if (submitText) submitText.textContent = 'Assign Transport';
            if (studentSelect) studentSelect.required = true;

            // Clear bulk selections
            document.querySelectorAll('input[name="students"]').forEach(cb => cb.checked = false);
            this.updateSelectedCount();
        } else {
            singleMode?.classList.add('hidden');
            multipleMode?.classList.remove('hidden');
            singleBtn?.classList.remove('bg-gradient-to-r', 'from-blue-500', 'to-indigo-600', 'text-white');
            singleBtn?.classList.add('text-gray-600', 'hover:text-gray-800');
            bulkBtn?.classList.add('bg-gradient-to-r', 'from-green-500', 'to-emerald-600', 'text-white');
            bulkBtn?.classList.remove('text-gray-600', 'hover:text-gray-800');
            
            if (modeInput) modeInput.value = 'bulk';
            if (submitText) submitText.textContent = 'Assign Multiple Students';
            if (studentSelect) {
                studentSelect.required = false;
                studentSelect.value = '';
            }
        }
    }

    // Update selected student count
    updateSelectedCount() {
        const selectedCheckboxes = document.querySelectorAll('input[name="students"]:checked');
        const countElement = document.getElementById('selectedCount');
        
        if (countElement) {
            countElement.textContent = selectedCheckboxes.length;
        }

        const submitText = document.getElementById('submitBtnText');
        const mode = document.getElementById('assignmentMode')?.value;
        
        if (mode === 'bulk' && selectedCheckboxes.length > 0) {
            submitText.textContent = `Assign ${selectedCheckboxes.length} Students`;
        }
    }

    // Select/Clear all students
    selectAllStudents() {
        document.querySelectorAll('input[name="students"]').forEach(checkbox => {
            checkbox.checked = true;
        });
        this.updateSelectedCount();
    }

    clearAllStudents() {
        document.querySelectorAll('input[name="students"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        this.updateSelectedCount();
    }

    // Form validation
    validateRouteName(e) {
        const input = e.target;
        const value = input.value.trim();
        
        this.clearFieldError(input);
        
        if (value.length > 0 && value.length < 2) {
            this.showFieldError(input, 'Route name must be at least 2 characters long.');
        } else if (value.length > 100) {
            this.showFieldError(input, 'Route name cannot exceed 100 characters.');
        }
    }

    validateStoppageName(e) {
        const input = e.target;
        const value = input.value.trim();
        
        this.clearFieldError(input);
        
        if (value.length > 0 && value.length < 2) {
            this.showFieldError(input, 'Stoppage name must be at least 2 characters long.');
        } else if (value.length > 100) {
            this.showFieldError(input, 'Stoppage name cannot exceed 100 characters.');
        }
    }

    showFieldError(field, message) {
        this.clearFieldError(field);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error text-red-500 text-sm mt-1';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
        field.classList.add('border-red-400');
    }

    clearFieldError(field) {
        const existingError = field.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
        field.classList.remove('border-red-400');
    }

    // Search functionality
    performSearch() {
        const query = document.getElementById('studentSearch')?.value.trim().toLowerCase();
        const mode = document.getElementById('assignmentMode')?.value || 'single';

        if (mode === 'single') {
            // Filter dropdown options
            const options = document.querySelectorAll('#student_id option');
            options.forEach(option => {
                if (option.value === '') return;
                const text = option.textContent.toLowerCase();
                option.style.display = text.includes(query) ? 'block' : 'none';
            });
        } else {
            // Filter checkbox list
            const studentLabels = document.querySelectorAll('input[name="students"]');
            studentLabels.forEach(checkbox => {
                const label = checkbox.closest('label');
                const text = label.textContent.toLowerCase();
                label.style.display = text.includes(query) ? 'flex' : 'none';
            });
        }
    }

    // Form submission handling
    handleAssignmentSubmit(e) {
        const form = e.target;
        const mode = document.getElementById('assignmentMode')?.value || 'single';
        const stoppageSelect = document.getElementById('id_stoppage');
        const studentSelect = document.getElementById('student_id');

        // Validate based on mode
        if (mode === 'single') {
            if (!studentSelect?.value) {
                e.preventDefault();
                this.showAlert('Please select a student.', 'error');
                studentSelect?.focus();
                return;
            }
        } else {
            const selectedStudents = document.querySelectorAll('input[name="students"]:checked');
            if (selectedStudents.length === 0) {
                e.preventDefault();
                this.showAlert('Please select at least one student.', 'error');
                return;
            }
        }

        if (!stoppageSelect?.value) {
            e.preventDefault();
            this.showAlert('Please select a stoppage.', 'error');
            stoppageSelect?.focus();
            return;
        }

        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
            submitBtn.disabled = true;
        }

        // For bulk mode, add selected students as hidden inputs
        if (mode === 'bulk') {
            studentSelect?.removeAttribute('required');
            const selectedStudents = document.querySelectorAll('input[name="students"]:checked');
            selectedStudents.forEach(checkbox => {
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'selected_students';
                hiddenInput.value = checkbox.value;
                form.appendChild(hiddenInput);
            });
        }
    }

    // Edit functions
    editRoute(id, name) {
        const routeForm = document.querySelector('form:has([name="route_submit"])');
        const nameField = routeForm?.querySelector('input[name="name"]');

        if (nameField) {
            nameField.value = name;
            nameField.focus();
        }

        document.getElementById('editRouteId').value = id;
        this.updateButton('routeSubmitIcon', 'routeSubmitText', 'fas fa-save mr-2', '✅ Update Route');
        this.showButton('routeCancelBtn');

        this.scrollToAndHighlight(routeForm, '#10B981');
    }

    editStoppage(id, name, routeId) {
        const stoppageForm = document.querySelector('form:has([name="stoppage_submit"])');
        const nameField = stoppageForm?.querySelector('input[name="name"]');
        const routeField = stoppageForm?.querySelector('select[name="route"]');

        if (nameField) {
            nameField.value = name;
            nameField.focus();
        }
        if (routeField) {
            routeField.value = routeId;
        }

        document.getElementById('editStoppageId').value = id;
        this.updateButton('stoppageSubmitIcon', 'stoppageSubmitText', 'fas fa-save mr-2', '✅ Update Stoppage');
        this.showButton('stoppageCancelBtn');

        this.scrollToAndHighlight(stoppageForm, '#8B5CF6');
    }

    editAssignment(id, studentId, stoppageId) {
        // Set form to single mode
        this.toggleAssignmentMode('single');

        const studentSelect = document.getElementById('student_id');
        const stoppageSelect = document.getElementById('id_stoppage');

        if (studentSelect) studentSelect.value = studentId || '';
        if (stoppageSelect) stoppageSelect.value = stoppageId || '';

        document.getElementById('editAssignmentId').value = id;
        this.updateButton('assignmentSubmitIcon', 'submitBtnText', 'fas fa-save mr-2', '✅ Update Assignment');
        this.showButton('assignmentCancelBtn');

        const assignmentForm = document.getElementById('assignmentForm');
        this.scrollToAndHighlight(assignmentForm, '#3B82F6');
    }

    // Cancel edit functions
    cancelRouteEdit() {
        const routeForm = document.querySelector('form:has([name="route_submit"])');
        routeForm?.reset();
        document.getElementById('editRouteId').value = '';
        this.updateButton('routeSubmitIcon', 'routeSubmitText', 'fas fa-plus mr-2', '➕ Add Route');
        this.hideButton('routeCancelBtn');
    }

    cancelStoppageEdit() {
        const stoppageForm = document.querySelector('form:has([name="stoppage_submit"])');
        stoppageForm?.reset();
        document.getElementById('editStoppageId').value = '';
        this.updateButton('stoppageSubmitIcon', 'stoppageSubmitText', 'fas fa-plus mr-2', '➕ Add Stoppage');
        this.hideButton('stoppageCancelBtn');
    }

    cancelAssignmentEdit() {
        const assignmentForm = document.getElementById('assignmentForm');
        
        document.getElementById('student_id').value = '';
        document.getElementById('id_stoppage').value = '';
        document.getElementById('editAssignmentId').value = '';

        this.updateButton('assignmentSubmitIcon', 'submitBtnText', 'fas fa-plus mr-2', 'Assign Transport');
        this.hideButton('assignmentCancelBtn');

        document.querySelectorAll('input[name="students"]').forEach(cb => cb.checked = false);
        this.updateSelectedCount();
    }

    // Utility functions
    updateButton(iconId, textId, iconClass, text) {
        const icon = document.getElementById(iconId);
        const textEl = document.getElementById(textId);
        
        if (icon) icon.className = iconClass;
        if (textEl) textEl.textContent = text;
    }

    showButton(buttonId) {
        const button = document.getElementById(buttonId);
        if (button) button.style.display = 'block';
    }

    hideButton(buttonId) {
        const button = document.getElementById(buttonId);
        if (button) button.style.display = 'none';
    }

    scrollToAndHighlight(element, color) {
        if (!element) return;
        
        element.scrollIntoView({ behavior: 'smooth' });
        
        const card = element.closest('.bg-white');
        if (card) {
            card.style.border = `3px solid ${color}`;
            card.style.boxShadow = `0 0 20px ${color}30`;
            setTimeout(() => {
                card.style.border = '';
                card.style.boxShadow = '';
            }, 3000);
        }
    }

    showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `fixed top-4 right-4 z-50 p-4 rounded-xl shadow-lg animate-slide-in ${
            type === 'error' ? 'bg-red-500' : 
            type === 'success' ? 'bg-green-500' : 
            'bg-blue-500'
        } text-white`;
        
        alertDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${
                    type === 'error' ? 'fa-exclamation-circle' : 
                    type === 'success' ? 'fa-check-circle' : 
                    'fa-info-circle'
                } mr-3"></i>
                <span class="font-medium">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-auto text-white hover:text-gray-200">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            alertDiv.style.opacity = '0';
            alertDiv.style.transform = 'translateX(100%)';
            setTimeout(() => alertDiv.remove(), 500);
        }, 5000);
    }

    autoHideMessages() {
        const messages = document.getElementById('form-messages');
        if (messages) {
            setTimeout(() => {
                messages.style.opacity = '0';
                messages.style.transform = 'translateX(100%)';
                setTimeout(() => messages.remove(), 500);
            }, 5000);
        }
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Confirmation dialog
    confirmDelete(type, name) {
        return confirm(`Are you sure you want to delete this ${type} "${name}"? This action cannot be undone.`);
    }

    // Stats card handlers
    showAssignmentStats() {
        const totalAssignments = document.querySelector('[data-stat="total-assignments"]')?.textContent || '0';
        const assignedStoppages = document.querySelector('[data-stat="assigned-stoppages"]')?.textContent || '0';
        this.showAlert(`🚌 Transport Assignments: ${totalAssignments}\n🚏 Assigned Stoppages: ${assignedStoppages}`, 'info');
    }

    showRouteStats() {
        const activeRoutes = document.querySelector('[data-stat="active-routes"]')?.textContent || '0';
        const totalStoppages = document.querySelector('[data-stat="total-stoppages"]')?.textContent || '0';
        this.showAlert(`🗺️ Active Routes: ${activeRoutes}\n🚏 Total Stoppages: ${totalStoppages}`, 'info');
    }

    showStoppageStats() {
        const totalStoppages = document.querySelector('[data-stat="total-stoppages"]')?.textContent || '0';
        const acrossRoutes = document.querySelector('[data-stat="across-routes"]')?.textContent || '0';
        this.showAlert(`🚏 Total Stoppages: ${totalStoppages}\n🗺️ Across Routes: ${acrossRoutes}`, 'info');
    }

    showStudentStats() {
        const totalStudents = document.querySelector('[data-stat="total-students"]')?.textContent || '0';
        const withTransport = document.querySelector('[data-stat="with-transport"]')?.textContent || '0';
        this.showAlert(`👥 Total Students: ${totalStudents}\n✅ With Transport: ${withTransport}`, 'info');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.transportManager = new TransportManager();
});

// Global functions for backward compatibility
function toggleAssignmentMode(mode) {
    window.transportManager?.toggleAssignmentMode(mode);
}

function selectAllStudents() {
    window.transportManager?.selectAllStudents();
}

function clearAllStudents() {
    window.transportManager?.clearAllStudents();
}

function editRoute(id, name) {
    window.transportManager?.editRoute(id, name);
}

function editStoppage(id, name, routeId) {
    window.transportManager?.editStoppage(id, name, routeId);
}

function editAssignment(id, studentId, stoppageId) {
    window.transportManager?.editAssignment(id, studentId, stoppageId);
}

function cancelRouteEdit() {
    window.transportManager?.cancelRouteEdit();
}

function cancelStoppageEdit() {
    window.transportManager?.cancelStoppageEdit();
}

function cancelAssignmentEdit() {
    window.transportManager?.cancelAssignmentEdit();
}

function confirmDelete(type, name) {
    return window.transportManager?.confirmDelete(type, name) || false;
}

function showAssignmentStats() {
    window.transportManager?.showAssignmentStats();
}

function showRouteStats() {
    window.transportManager?.showRouteStats();
}

function showStoppageStats() {
    window.transportManager?.showStoppageStats();
}

function showStudentStats() {
    window.transportManager?.showStudentStats();
}