// Enhanced Fee Payment Handler
console.log("🚀 Fee Payment Handler loaded");

// Global payment confirmation functions
let currentForm = null;
let currentButton = null;

window.showPaymentConfirmation = function(studentName, studentClass, button) {
    console.log("💳 showPaymentConfirmation called", { studentName, studentClass });
    
    const form = button.closest('form');
    if (!form) {
        console.error("❌ Form not found for button");
        return;
    }
    
    const fees = form.querySelectorAll('.fee-checkbox:checked');
    
    if (fees.length === 0) {
        window.showMessage('Please select at least one fee to pay.', 'error');
        return;
    }
    
    const mode = form.querySelector('#payment_mode').value;
    if (!mode) {
        window.showMessage('Please select a payment method.', 'error');
        return;
    }
    
    // Store references
    currentForm = form;
    currentButton = button;
    
    // Get amounts from summary
    const totalSelected = document.getElementById('total_selected').textContent;
    const totalDiscount = document.getElementById('total_discount').textContent;
    const totalPayable = document.getElementById('total_payable').textContent;
    
    // Populate modal
    document.getElementById('confirmStudentName').textContent = studentName;
    document.getElementById('confirmClass').textContent = studentClass;
    document.getElementById('confirmTotalAmount').textContent = totalSelected;
    document.getElementById('confirmDiscount').textContent = totalDiscount;
    document.getElementById('confirmPayableAmount').textContent = totalPayable;
    
    // Show modal with auto scroll
    const modal = document.getElementById('paymentConfirmModal');
    modal.classList.remove('hidden');
    
    // Auto scroll to show full modal
    setTimeout(() => {
        modal.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
};

window.closePaymentConfirmation = function() {
    document.getElementById('paymentConfirmModal').classList.add('hidden');
    currentForm = null;
    currentButton = null;
};

window.processConfirmedPayment = async function() {
    if (!currentForm || !currentButton) {
        console.error("❌ No form or button reference");
        return;
    }
    
    console.log("🔄 Processing confirmed payment");
    
    // Store references before closing modal
    const form = currentForm;
    const button = currentButton;
    
    // Close modal
    closePaymentConfirmation();
    
    const fees = form.querySelectorAll('.fee-checkbox:checked');
    console.log("📋 Selected fees:", fees.length);
    
    if (fees.length === 0) {
        window.showMessage('No fees selected for payment', 'error');
        return;
    }
    
    // Prepare form data
    fees.forEach(checkbox => {
        const row = checkbox.closest('.fee-row');
        const amountCell = row.querySelector('.fee-amount');
        
        if (amountCell) {
            let originalAmount;
            if (checkbox.value === 'carry_forward') {
                const cfInput = form.querySelector('input[name="amount_carry_forward"]');
                originalAmount = cfInput ? cfInput.value : amountCell.textContent.replace(/[^0-9.]/g, '');
            } else {
                originalAmount = amountCell.textContent.replace(/[^0-9.]/g, '');
            }
            
            const discountInput = row.querySelector('.discount-input');
            const discount = discountInput ? (discountInput.value || '0') : '0';
            
            console.log(`💰 Fee ${checkbox.value}: Amount=${originalAmount}, Discount=${discount}`);
            
            // Remove existing hidden inputs
            const existingAmount = form.querySelector(`input[name="amount_${checkbox.value}"]`);
            if (existingAmount) existingAmount.remove();
            
            const existingDiscount = form.querySelector(`input[name="discount_${checkbox.value}"]`);
            if (existingDiscount) existingDiscount.remove();
            
            // Add amount input
            const amountInput = document.createElement('input');
            amountInput.type = 'hidden';
            amountInput.name = 'amount_' + checkbox.value;
            amountInput.value = originalAmount;
            form.appendChild(amountInput);
            
            // Add discount input if applicable
            if (parseFloat(discount) > 0) {
                const discountHidden = document.createElement('input');
                discountHidden.type = 'hidden';
                discountHidden.name = 'discount_' + checkbox.value;
                discountHidden.value = discount;
                form.appendChild(discountHidden);
            }
        }
    });
    
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
    button.disabled = true;
    
    try {
        const formData = new FormData(form);
        
        // Debug form data
        console.log("📊 Form data being sent:");
        for (let [key, value] of formData.entries()) {
            console.log(`  ${key}: ${value}`);
        }
        
        // Get CSRF token from form
        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]')?.value;
        console.log('🔐 CSRF token:', csrfToken ? 'Found' : 'Missing');
        
        if (!csrfToken) {
            // Try to get CSRF token from page cookies
            const cookieToken = getCookie('csrftoken');
            if (cookieToken) {
                console.log('🔐 Using CSRF token from cookie');
                formData.append('csrfmiddlewaretoken', cookieToken);
            } else {
                console.error('❌ CSRF token required but not found');
                window.showMessage('Security token missing. Please refresh the page.', 'error');
                return;
            }
        }
        
        // Ensure payment date is set
        const paymentDateField = form.querySelector('#deposit_date');
        if (!paymentDateField?.value) {
            // Set current date and time if not already set
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const currentDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
            paymentDateField.value = currentDateTime;
            console.log('📅 Payment date auto-set to:', currentDateTime);
        }
        
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        console.log("🌐 Response status:", response.status);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        console.log("📦 Payment response:", result);
        
        if (result.status === 'success') {
            window.showMessage(`Payment successful! Receipt: ${result.receipt_no}, Amount: ₹${result.total_paid}`, 'success');
            setTimeout(() => {
                if (result.redirect_url) {
                    window.location.href = result.redirect_url;
                } else {
                    // Fallback redirect
                    window.location.reload();
                }
            }, 1500);
        } else {
            console.error("❌ Payment failed:", result);
            window.showMessage(result.message || 'Payment failed', 'error');
        }
    } catch (error) {
        console.error("❌ Payment error:", error);
        window.showMessage(`Network error: ${error.message}`, 'error');
    } finally {
        button.innerHTML = '<i class="fas fa-credit-card mr-3 text-xl"></i>💳 Confirm Payment';
        button.disabled = false;
    }
};

// Global message function
window.showMessage = function(message, type = 'info') {
    // Remove existing messages
    const existingMsg = document.getElementById('payment-message');
    if (existingMsg) existingMsg.remove();
    
    const messageEl = document.createElement('div');
    messageEl.id = 'payment-message';
    messageEl.className = 'fixed top-4 right-4 z-50 p-4 rounded-xl shadow-lg transition-all duration-300';
    
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
    
    messageEl.className += ` ${colors[type] || colors.info}`;
    messageEl.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${icons[type] || icons.info} mr-3"></i>
            <span class="font-medium">${message}</span>
        </div>
    `;
    
    document.body.appendChild(messageEl);
    
    // Auto-hide after 5 seconds for non-error messages
    if (type !== 'error') {
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.style.opacity = '0';
                messageEl.style.transform = 'translateX(100%)';
                setTimeout(() => messageEl.remove(), 300);
            }
        }, 5000);
    }
};

// Helper function for cookie (if needed)
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

console.log("✅ Fee Payment Handler initialized");