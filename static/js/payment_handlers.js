// D:\School-Management-System\School-Management-System-main\student_fees\static\js\payment_handlers.js
// Handle payment processing

import { getCSRFToken, showFormError } from './core.js';
// console.log("payment_handlers.js loaded");

export async function handleFeeFormSubmit(form) {
    // console.log("handleFeeFormSubmit called for form:", form.id);
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalContent = submitBtn.innerHTML;

    // Prevent double submission
    if (submitBtn.disabled) {
        // console.log("Submit button is disabled. Aborting submission.");
        return;
    }

    try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Processing...';
        // console.log("Submitting fee form:", form.id);

        if (!validatePaymentForm(form)) {
            submitBtn.innerHTML = originalContent;
            submitBtn.disabled = false;
            // console.log("Payment form validation failed for form:", form.id);
            return;
        }

        const formData = prepareFormData(form);
        // console.log("Prepared formData for submission:", formData);
        const response = await submitPayment(formData);
        // console.log("Payment response received:", response);

        if (response.redirect_url) {
            window.location.href = response.redirect_url;
        } else {
            window.location.reload();
        }
    } catch (error) {
        // console.error('Payment error:', error);
        showFormError(form, error.message);
        submitBtn.innerHTML = originalContent;
        submitBtn.disabled = false;
    }
}

function validatePaymentForm(form) {
    // Check payment mode
    const paymentModeEl = form.querySelector('#payment_mode');
    if (!paymentModeEl) {
        showFormError(form, 'Payment mode selection is required');
        return false;
    }
    const paymentMode = paymentModeEl.value;

    // Check if any fees are selected
    if (form.querySelectorAll('.fee-checkbox:checked').length === 0) {
        showFormError(form, 'Please select at least one fee to pay');
        return false;
    }

    // Validate non-cash payments
    if (paymentMode !== 'Cash') {
        const transactionNo = form.querySelector('input[name="transaction_no"]')?.value;
        const paymentSource = form.querySelector('input[name="payment_source"]')?.value;

        if (!transactionNo || !paymentSource) {
            showFormError(form, 'Transaction details are required for non-cash payments');
            return false;
        }
    }

    // Validate CF payment if selected
    const cfCheckbox = form.querySelector('.fee-checkbox[value="carry_forward"]');
    const hasCF = cfCheckbox && cfCheckbox.checked;
    
    if (hasCF) {
        const cfAmountInput = form.querySelector('[name="amount_carry_forward"]');
        if (!cfAmountInput) {
            showFormError(form, 'Carry Forward amount field is missing');
            return false;
        }

        const cfAmount = parseFloat(cfAmountInput.value);
        const cfDiscount = parseFloat(form.querySelector('[name="discount_carry_forward"]')?.value || '0');
        
        if (isNaN(cfAmount)) {
            showFormError(form, 'Invalid Carry Forward amount');
            return false;
        }
        
        if (cfDiscount > cfAmount) {
            showFormError(form, 'Discount cannot exceed Carry Forward amount');
            return false;
        }
    }
    
    // console.log("Payment form validated successfully for form:", form.id);
    return true;
}

function prepareFormData(form) {
    const formData = new FormData(form);
    const studentId = form.querySelector('input[name="student_id"]').value;
    formData.append('student_id', studentId);

    let payable = 0;
    form.querySelectorAll('.fee-checkbox:checked').forEach(checkbox => {
        const feeId = checkbox.value;
        const row = checkbox.closest('.fee-row');
        const discountInput = row.querySelector('.discount-input');
        const discount = parseFloat(discountInput?.value || '0');
        
        let amount;
        // console.log(`Processing fee ${feeId}`);

        if (feeId === 'carry_forward') {
            // Method 1: Get from checkbox's next sibling (hidden input)
            if (checkbox.nextElementSibling && 
                checkbox.nextElementSibling.name === "amount_carry_forward") {
                amount = parseFloat(checkbox.nextElementSibling.value);
            }
            // Method 2: Get from form-level hidden input
            else if (form.querySelector('[name="amount_carry_forward"]')) {
                amount = parseFloat(form.querySelector('[name="amount_carry_forward"]').value);
            }
            // Method 3: Fallback to fee-amount cell
            else {
                const amountCell = row.querySelector('.fee-amount');
                amount = parseFloat(amountCell?.textContent.replace(/[^0-9.]/g, '')) || 0;
            }
            
            // console.log('Carry Forward Amount:', amount);
            formData.append('amount_carry_forward', amount.toFixed(2));
            formData.append('discount_carry_forward', discount.toFixed(2));
        } else {
            amount = parseFloat(checkbox.dataset.amount);
            formData.append('selected_fees', feeId);
            formData.append(`amount_${feeId}`, amount.toFixed(2));
            formData.append(`discount_${feeId}`, discount.toFixed(2));
            payable += (amount - discount);
        }
    });

    formData.append('paid_amount', payable.toFixed(2));
    return formData;
}


async function submitPayment(formData) {
    // console.log("submitPayment called");
    const response = await fetch('/student_fees/submit-deposit/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        }
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Server error: ${response.status} - ${errorText}`);
    }

    return await response.json();
}