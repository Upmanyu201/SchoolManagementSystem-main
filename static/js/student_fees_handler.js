// Student Fees Handler - Minimal implementation for deposit.html
console.log("🎓 Student Fees Handler loaded");

document.addEventListener('DOMContentLoaded', function() {
    console.log("📚 DOM loaded, initializing student fees handlers");
    
    // Handle "Process Payment" button clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('view-fees-btn') || e.target.closest('.view-fees-btn')) {
            const button = e.target.classList.contains('view-fees-btn') ? e.target : e.target.closest('.view-fees-btn');
            const studentId = button.getAttribute('data-student-id');
            const admissionNumber = button.getAttribute('data-admission-number');
            
            console.log(`💰 Processing payment for student ${admissionNumber} (ID: ${studentId})`);
            
            loadStudentFees(studentId, admissionNumber, button);
        }
    });
    
    // Handle discount toggle
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('discount-toggle')) {
            const studentCard = e.target.closest('.student-card');
            const studentId = studentCard.getAttribute('data-student-id');
            const admissionNumber = studentCard.querySelector('.view-fees-btn').getAttribute('data-admission-number');
            
            console.log(`🏷️ Discount toggle changed for student ${admissionNumber}`);
            
            // Reload fees with discount setting
            const container = document.getElementById(`fees-container-${admissionNumber}`);
            if (container && !container.classList.contains('hidden')) {
                loadStudentFees(studentId, admissionNumber, null, e.target.checked);
            }
        }
    });
});

async function loadStudentFees(studentId, admissionNumber, button, discountEnabled = false) {
    const container = document.getElementById(`fees-container-${admissionNumber}`);
    
    if (!container) {
        console.error(`❌ Container not found for student ${admissionNumber}`);
        return;
    }
    
    // Show container and loading state
    container.classList.remove('hidden');
    container.innerHTML = `
        <div class="border-2 border-dashed border-blue-300 rounded-xl p-8 loading-container text-center">
            <div class="flex justify-center mb-4">
                <div class="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
            </div>
            <p class="text-lg font-semibold text-gray-700 flex items-center justify-center">
                <i class="fas fa-spinner fa-spin mr-2 text-blue-500"></i>
                Loading fees data...
            </p>
        </div>
    `;
    
    // Update button state
    if (button) {
        const originalText = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Loading...';
        button.disabled = true;
        
        // Restore button after 3 seconds
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 3000);
    }
    
    try {
        // Get discount setting from toggle
        const discountToggle = document.getElementById(`discount-toggle-${studentId}`);
        const isDiscountEnabled = discountToggle ? discountToggle.checked : discountEnabled;
        
        const url = `/student_fees/ajax/get-student-fees/?admission_number=${encodeURIComponent(admissionNumber)}&isDiscountEnabled=${isDiscountEnabled}`;
        console.log(`🌐 Fetching fees from: ${url}`);
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json'
            }
        });
        
        console.log(`📡 Response status: ${response.status}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`📦 Received data:`, data);
        
        if (data.status === 'success') {
            container.innerHTML = data.html;
            console.log(`✅ Fees loaded successfully for student ${admissionNumber}`);
            
            // Initialize totals calculation after content is loaded
            setTimeout(() => {
                initializeFeesTotals(admissionNumber);
                container.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'nearest' 
                });
            }, 100);
        } else {
            throw new Error(data.message || 'Failed to load fees');
        }
        
    } catch (error) {
        console.error(`❌ Error loading fees for student ${admissionNumber}:`, error);
        
        container.innerHTML = `
            <div class="border-2 border-dashed border-red-300 rounded-xl p-8 text-center bg-red-50">
                <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-exclamation-triangle text-red-500 text-2xl"></i>
                </div>
                <h3 class="text-lg font-bold text-red-700 mb-2">Error Loading Fees</h3>
                <p class="text-red-600 mb-4">${error.message}</p>
                <button onclick="loadStudentFees('${studentId}', '${admissionNumber}', null, ${discountEnabled})" 
                        class="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded-lg transition-colors">
                    <i class="fas fa-redo mr-2"></i>Try Again
                </button>
            </div>
        `;
    }
}

// Initialize totals calculation for loaded fees
function initializeFeesTotals(admissionNumber) {
    console.log(`📊 Initializing totals for student ${admissionNumber}`);
    
    const form = document.getElementById(`depositForm-${admissionNumber}`);
    if (!form) {
        console.error(`❌ Form not found: depositForm-${admissionNumber}`);
        return;
    }
    
    // Get CSRF token
    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
    }
    
    // Payment summary calculation
    function updateTotals() {
        console.log('=== updateTotals called ===');
        
        let selectedTotal = 0;
        let totalDiscount = 0;
        
        // Debug: Check if elements exist
        const totalSelectedEl = document.getElementById('total_selected');
        const totalDiscountEl = document.getElementById('total_discount');
        const totalPayableEl = document.getElementById('total_payable');
        
        console.log('Summary elements found:', {
            totalSelected: !!totalSelectedEl,
            totalDiscount: !!totalDiscountEl,
            totalPayable: !!totalPayableEl
        });
        
        // Calculate selected fees total
        const checkedBoxes = form.querySelectorAll('.fee-checkbox:checked');
        console.log('Checked boxes count:', checkedBoxes.length);
        
        checkedBoxes.forEach((checkbox, index) => {
            const amount = parseFloat(checkbox.getAttribute('data-amount')) || 0;
            console.log(`Checkbox ${index}: value=${checkbox.value}, amount=${amount}`);
            selectedTotal += amount;
        });
        
        console.log('Selected total calculated:', selectedTotal);
        
        // Calculate total discount (only for checked fees)
        const allCheckboxes = form.querySelectorAll('.fee-checkbox');
        console.log('All checkboxes count:', allCheckboxes.length);
        
        allCheckboxes.forEach((checkbox, index) => {
            if (checkbox.checked) {
                const row = checkbox.closest('.fee-row');
                const discountInput = row ? row.querySelector('.discount-input') : null;
                if (discountInput) {
                    const discount = parseFloat(discountInput.value) || 0;
                    console.log(`Discount for checkbox ${index}: ${discount}`);
                    totalDiscount += discount;
                }
            }
        });
        
        console.log('Total discount calculated:', totalDiscount);
        
        // Update payable amounts in each row
        form.querySelectorAll('.fee-row').forEach((row, index) => {
            const checkbox = row.querySelector('.fee-checkbox');
            const payableCell = row.querySelector('.payable-amount');
            const discountInput = row.querySelector('.discount-input');
            
            if (checkbox && payableCell) {
                const originalAmount = parseFloat(checkbox.getAttribute('data-amount')) || 0;
                const discount = discountInput ? (parseFloat(discountInput.value) || 0) : 0;
                const payableAmount = Math.max(0, originalAmount - discount);
                payableCell.textContent = `₹ ${payableAmount.toFixed(2)}`;
                console.log(`Row ${index} payable updated: ${payableAmount}`);
            }
        });
        
        const totalPayable = Math.max(0, selectedTotal - totalDiscount);
        console.log('Final totals:', { selectedTotal, totalDiscount, totalPayable });
        
        // Update summary totals
        if (totalSelectedEl) {
            totalSelectedEl.textContent = `₹ ${selectedTotal.toFixed(2)}`;
            console.log('Updated total_selected element');
        }
        if (totalDiscountEl) {
            totalDiscountEl.textContent = `₹ ${totalDiscount.toFixed(2)}`;
            console.log('Updated total_discount element');
        }
        if (totalPayableEl) {
            totalPayableEl.textContent = `₹ ${totalPayable.toFixed(2)}`;
            console.log('Updated total_payable element');
        }
        
        console.log('=== updateTotals completed ===');
    }
    
    // Add event listeners for checkboxes
    const checkboxes = form.querySelectorAll('.fee-checkbox');
    console.log('Found checkboxes:', checkboxes.length);
    
    checkboxes.forEach((checkbox, index) => {
        console.log(`Adding listener to checkbox ${index}:`, checkbox.value);
        checkbox.addEventListener('change', function() {
            console.log(`Checkbox ${index} changed: ${this.value} = ${this.checked}`);
            updateTotals();
        });
    });
    
    // Add event listeners for discount inputs
    const discountInputs = form.querySelectorAll('.discount-input');
    console.log('Found discount inputs:', discountInputs.length);
    
    discountInputs.forEach((input, index) => {
        console.log(`Adding listener to discount input ${index}:`, input.name);
        
        input.addEventListener('input', function() {
            console.log(`Discount input ${index} changed: ${this.name} = ${this.value}`);
            const maxAmount = parseFloat(this.getAttribute('max')) || 0;
            const currentValue = parseFloat(this.value) || 0;
            
            // Ensure discount doesn't exceed fee amount
            if (currentValue > maxAmount) {
                this.value = maxAmount;
                console.log(`Discount capped at max: ${maxAmount}`);
            }
            
            updateTotals();
        });
        
        // Also listen for keyup for real-time updates
        input.addEventListener('keyup', function() {
            console.log(`Discount input ${index} keyup: ${this.name} = ${this.value}`);
            updateTotals();
        });
    });
    
    // Form submission handling
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const selectedFees = form.querySelectorAll('.fee-checkbox:checked');
        if (selectedFees.length === 0) {
            alert('Please select at least one fee to pay.');
            return;
        }
        
        const paymentMode = form.querySelector('#payment_mode')?.value;
        if (!paymentMode) {
            alert('Please select a payment method.');
            return;
        }
        
        const depositDate = form.querySelector('#deposit_date')?.value;
        if (!depositDate) {
            alert('Please select a payment date.');
            return;
        }
        
        // Submit form with CSRF token
        submitPaymentForm(form);
    });
    
    // Payment form submission
    async function submitPaymentForm(form) {
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
        submitBtn.disabled = true;
        
        try {
            const formData = new FormData(form);
            const csrfToken = getCSRFToken();
            
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                }
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                alert(`Payment successful! Receipt: ${result.receipt_no}`);
                if (result.redirect_url) {
                    window.location.href = result.redirect_url;
                } else {
                    window.location.reload();
                }
            } else {
                alert(result.message || 'Payment failed');
            }
        } catch (error) {
            console.error('Payment error:', error);
            alert('Payment failed: ' + error.message);
        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }
    
    // Initial calculation
    console.log('Calling initial updateTotals...');
    updateTotals();
    
    console.log(`✅ Totals calculation initialized for ${admissionNumber}`);
}

// Make functions globally available
window.loadStudentFees = loadStudentFees;
window.initializeFeesTotals = initializeFeesTotals;

console.log("✅ Student Fees Handler initialized");