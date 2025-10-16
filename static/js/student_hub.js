// static/js/student_hub.js
class StudentHub {
    constructor(admissionNumber) {
        this.admissionNumber = admissionNumber;
        this.data = null;
        this.modules = new Map();
        this.eventBus = new EventTarget();
        this.refreshInterval = null;
    }
    
    async initialize() {
        try {
            await this.loadStudentData();
            this.setupModules();
            this.setupEventListeners();
            this.render();
            this.startAutoRefresh();
        } catch (error) {
            this.handleError(error);
        }
    }
    
    async loadStudentData() {
        try {
            const response = await fetch(`/students/api/dashboard/${this.admissionNumber}/`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.data = await response.json();
            this.updateUI();
        } catch (error) {
            console.error('Failed to load student data:', error);
            this.handleError(error);
        }
    }
    
    setupModules() {
        this.modules.set('fees', new FeesModule(this));
        this.modules.set('attendance', new AttendanceModule(this));
        this.modules.set('transport', new TransportModule(this));
        this.modules.set('results', new ResultsModule(this));
    }
    
    setupEventListeners() {
        // Payment success handler
        this.eventBus.addEventListener('paymentSuccess', (event) => {
            this.showMessage('Payment processed successfully!', 'success');
            this.refreshData();
        });
        
        // Payment error handler
        this.eventBus.addEventListener('paymentError', (event) => {
            this.showMessage(`Payment failed: ${event.detail}`, 'error');
        });
        
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
    }
    
    async processPayment(paymentData) {
        try {
            const response = await fetch(`/students/api/payment/${this.admissionNumber}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(paymentData)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.eventBus.dispatchEvent(new CustomEvent('paymentSuccess', {
                    detail: result
                }));
            } else {
                throw new Error(result.error);
            }
            
        } catch (error) {
            this.eventBus.dispatchEvent(new CustomEvent('paymentError', {
                detail: error.message
            }));
        }
    }
    
    async refreshData() {
        await this.loadStudentData();
        this.modules.forEach(module => module.refresh(this.data));
    }
    
    switchTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('active');
        });
        
        // Remove active class from all buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Show selected tab
        document.getElementById(`${tabName}-tab`).classList.add('active');
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // Load module data if needed
        const module = this.modules.get(tabName);
        if (module && !module.loaded) {
            module.load();
        }
    }
    
    updateUI() {
        if (!this.data) {
            console.warn('No dashboard data available');
            return;
        }
        
        // Update header information
        this.updateHeader();
        
        // Update financial summary
        this.updateFinancialSummary();
        
        // Update recent activities
        this.updateRecentActivities();
    }
    
    updateHeader() {
        const profile = this.data.profile || {};
        
        const nameEl = document.querySelector('.student-name');
        const detailsEl = document.querySelector('.student-details');
        const avatarEl = document.querySelector('.student-avatar');
        
        if (nameEl && profile.name) {
            nameEl.textContent = profile.name;
        }
        
        if (detailsEl && profile.admission_number) {
            detailsEl.textContent = `${profile.admission_number} | ${profile.class || 'N/A'}-${profile.section || 'N/A'}`;
        }
        
        if (avatarEl && profile.photo) {
            avatarEl.src = profile.photo;
        }
    }
    
    updateFinancialSummary() {
        const financial = this.data.financial || {};
        
        const currentDuesEl = document.querySelector('.current-dues');
        const totalBalanceEl = document.querySelector('.total-balance');
        const lastPaymentEl = document.querySelector('.last-payment');
        
        if (currentDuesEl) {
            currentDuesEl.textContent = `₹${financial.current_dues || 0}`;
        }
        
        if (totalBalanceEl) {
            totalBalanceEl.textContent = `₹${financial.total_balance || 0}`;
        }
        
        if (lastPaymentEl && financial.last_payment) {
            lastPaymentEl.textContent = `₹${financial.last_payment.amount} on ${financial.last_payment.date}`;
        }
    }
    
    updateRecentActivities() {
        const activities = this.data.recent_activities || [];
        const container = document.querySelector('.recent-activities');
        
        if (!container) return;
        
        if (activities.length === 0) {
            container.innerHTML = '<p class="text-muted">No recent activities</p>';
            return;
        }
        
        container.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <i class="${activity.icon || 'fas fa-circle'} text-${activity.color || 'primary'}"></i>
                <div class="activity-content">
                    <p class="activity-description">${activity.description || 'Activity'}</p>
                    <small class="activity-date">${activity.date || 'Unknown date'}</small>
                </div>
            </div>
        `).join('');
    }
    
    startAutoRefresh() {
        // Refresh data every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.refreshData();
        }, 300000);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
    
    showMessage(message, type = 'info') {
        const messageContainer = document.getElementById('messages');
        const messageElement = document.createElement('div');
        messageElement.className = `alert alert-${type} alert-dismissible fade show`;
        messageElement.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        messageContainer.appendChild(messageElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageElement.remove();
        }, 5000);
    }
    
    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    handleError(error) {
        console.error('StudentHub Error:', error);
        this.showMessage('An error occurred while loading student data', 'error');
    }
    
    destroy() {
        this.stopAutoRefresh();
        this.modules.forEach(module => module.destroy());
    }
}

// Module base class
class StudentModule {
    constructor(studentHub) {
        this.studentHub = studentHub;
        this.loaded = false;
    }
    
    refresh(data) {
        // Override in subclasses
    }
    
    load() {
        // Override in subclasses
        this.loaded = true;
    }
    
    destroy() {
        // Override in subclasses
    }
}

// Fees Module
class FeesModule extends StudentModule {
    refresh(data) {
        this.updateFeesDisplay(data.financial);
    }
    
    updateFeesDisplay(financial) {
        // Update fees-specific UI elements
        const feesTab = document.getElementById('fees-tab');
        if (feesTab) {
            feesTab.querySelector('.dues-amount').textContent = `₹${financial.current_dues}`;
            feesTab.querySelector('.fines-amount').textContent = `₹${financial.unpaid_fines}`;
        }
    }
}

// Attendance Module
class AttendanceModule extends StudentModule {
    refresh(data) {
        this.updateAttendanceDisplay(data.academic);
    }
    
    updateAttendanceDisplay(academic) {
        const attendanceTab = document.getElementById('attendance-tab');
        if (attendanceTab) {
            attendanceTab.querySelector('.attendance-percentage').textContent = 
                `${academic.attendance_percentage}%`;
        }
    }
}

// Transport Module
class TransportModule extends StudentModule {
    refresh(data) {
        // Update transport information
    }
}

// Results Module
class ResultsModule extends StudentModule {
    refresh(data) {
        this.updateResultsDisplay(data.academic);
    }
    
    updateResultsDisplay(academic) {
        // Update results display
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const studentDashboard = document.getElementById('studentDashboard');
    if (studentDashboard) {
        const admissionNumber = studentDashboard.dataset.admission;
        const studentHub = new StudentHub(admissionNumber);
        studentHub.initialize();
        
        // Store reference for cleanup
        window.studentHub = studentHub;
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.studentHub) {
        window.studentHub.destroy();
    }
});