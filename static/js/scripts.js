// C:\xampp\htdocs\school_management\static\js\scripts.js
document.addEventListener("DOMContentLoaded", function() {
    console.log("✅ School Management System scripts loaded");
    
    // Initialize tooltips
    initTooltips();
    
    // Initialize modals
    initModals();
    
    // Initialize forms
    initForms();
    
    // Initialize tables
    initTables();
    
    // Initialize charts if they exist
    initCharts();
});

function initTooltips() {
    const tooltipTriggers = document.querySelectorAll('[data-tooltip]');
    
    tooltipTriggers.forEach(trigger => {
        const tooltipId = trigger.getAttribute('aria-describedby');
        const tooltip = document.getElementById(tooltipId);
        
        if (!tooltip) return;
        
        trigger.addEventListener('mouseenter', () => {
            tooltip.classList.remove('invisible', 'opacity-0');
            tooltip.classList.add('visible', 'opacity-100');
        });
        
        trigger.addEventListener('mouseleave', () => {
            tooltip.classList.remove('visible', 'opacity-100');
            tooltip.classList.add('invisible', 'opacity-0');
        });
    });
}

function initModals() {
    // Open modal function
    window.openModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }
    };
    
    // Close modal function
    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }
    };
    
    // Close modals when clicking outside
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
                document.body.classList.remove('overflow-hidden');
            }
        });
    });
}

function initForms() {
    // Add loading state to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <span class="inline-flex items-center">
                        <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                    </span>
                `;
            }
        });
    });
}

function initTables() {
    // Search functionality for all tables with search
    document.querySelectorAll('.searchable-table').forEach(table => {
        const searchBox = table.querySelector('.table-search');
        if (!searchBox) return;
        
        searchBox.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = table.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const rowText = row.textContent.toLowerCase();
                row.style.display = rowText.includes(searchTerm) ? '' : 'none';
            });
        });
    });
    
    // Sortable tables
    document.querySelectorAll('.sortable-table th[data-sort]').forEach(header => {
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const columnIndex = this.cellIndex;
            const isAscending = !this.classList.contains('asc');
            
            // Reset all headers
            table.querySelectorAll('th[data-sort]').forEach(th => {
                th.classList.remove('asc', 'desc');
            });
            
            // Set current header state
            this.classList.toggle('asc', isAscending);
            this.classList.toggle('desc', !isAscending);
            
            // Sort the table
            sortTable(table, columnIndex, isAscending);
        });
    });
}

function sortTable(table, columnIndex, isAscending) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        // Numeric sorting
        if (!isNaN(aValue) && !isNaN(bValue)) {
            return isAscending ? aValue - bValue : bValue - aValue;
        }
        
        // String sorting
        return isAscending 
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
    });
    
    // Reattach sorted rows
    rows.forEach(row => tbody.appendChild(row));
}

function initCharts() {
    // Initialize any charts on the page
    if (typeof Chart !== 'undefined') {
        document.querySelectorAll('[data-chart]').forEach(chartEl => {
            const config = JSON.parse(chartEl.getAttribute('data-chart'));
            new Chart(chartEl, config);
        });
    }
}

// Utility functions
window.showLoading = function(elementId = 'loadingSpinner') {
    const spinner = document.getElementById(elementId);
    if (spinner) spinner.classList.remove('hidden');
};

window.hideLoading = function(elementId = 'loadingSpinner') {
    const spinner = document.getElementById(elementId);
    if (spinner) spinner.classList.add('hidden');
};