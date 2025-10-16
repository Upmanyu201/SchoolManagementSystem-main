// student_fees/static/student_fees/js/form_handlers.js

import { getCSRFToken, showFormError } from './core.js';
import { showConfirmationModal } from './modal_handlers.js';
import { handleFeeFormSubmit } from './payment_handlers.js';
import { updateFeeCalculations } from './fee_calculations.js';

// console.log("form_handlers.js loaded");

// Initialize all form handlers
export function initializeFormHandlers() {
    // console.log("initializeFormHandlers called");
    // Handle discount inputs
    document.addEventListener('input', function(e) {
        if (e.target.matches('.discount-input')) {
            // console.log("Discount input changed:", e.target);
            validateDiscountInput(e.target);
            const form = e.target.closest('form');
            if (form) {
                // console.log("Updating fee calculations for form:", form.id);
                updateFeeCalculations(form);
            }
        }
    });

    // Handle payment mode changes
    document.addEventListener('change', function(e) {
        if (e.target.matches('#payment_mode')) {
            // console.log("Payment mode changed to:", e.target.value);
            handlePaymentModeChange(e.target);
        }
    });

    // Note: Form submissions now handled by enhanced form handler
}

// Validate discount input
function validateDiscountInput(input) {
    // console.log("Validating discount input:", input);
    const maxDiscount = parseFloat(input.max) || 0;
    const currentValue = parseFloat(input.value) || 0;

    if (currentValue > maxDiscount) {
        input.value = maxDiscount;
        showFormError(input.closest('form'), `Discount cannot exceed ₹${maxDiscount}`);
    }
}

// Handle payment mode change
export function handlePaymentModeChange(selectElement) {
    console.log("handlePaymentModeChange called with:", selectElement.value);
    const form = selectElement.closest('form');
    const paymentFields = form?.querySelector('#extra_fields');
    const paymentMode = selectElement.value;

    if (!paymentFields) {
        console.log("Payment fields not found in form:", form?.id || 'unknown');
        return;
    }

    // Show/hide fields based on payment mode
    if (paymentMode === 'Cash') {
        paymentFields.style.display = 'none';
    } else {
        paymentFields.style.display = 'grid';
        updatePaymentFieldLabels(paymentFields, paymentMode);
    }
}

// Update payment field labels based on mode
function updatePaymentFieldLabels(paymentFields, paymentMode) {
    const sourceLabel = paymentFields.querySelector('#source_label');
    const numberInput = paymentFields.querySelector('#trans_no');

    if (!sourceLabel || !numberInput) return;

    switch (paymentMode) {
        case 'Cheque':
            sourceLabel.innerHTML = '<i class="fas fa-university mr-2 text-teal-500"></i>🏦 Bank Name';
            numberInput.placeholder = 'Cheque Number';
            break;
        case 'Online':
            sourceLabel.innerHTML = '<i class="fas fa-globe mr-2 text-teal-500"></i>🌐 Bank/Platform';
            numberInput.placeholder = 'Transaction ID';
            break;
        case 'UPI':
            sourceLabel.innerHTML = '<i class="fas fa-mobile-alt mr-2 text-teal-500"></i>📱 UPI App';
            numberInput.placeholder = 'UPI Reference';
            break;
        case 'Card':
            sourceLabel.innerHTML = '<i class="fas fa-credit-card mr-2 text-teal-500"></i>💳 Card Issuer';
            numberInput.placeholder = 'Last 4 digits';
            break;
    }
}

// Initialize a fee form
export function initializeFeeForm(form) {
    // console.log("initializeFeeForm called for form:", form.id);
    form.querySelectorAll('.fee-checkbox').forEach(cb => {
        cb.addEventListener('change', () => {
            // console.log("Fee-checkbox changed:", cb);
            updateFeeCalculations(form);
        });
    });

    const discountToggle = form.querySelector('.discount-toggle');
    if (discountToggle) {
        discountToggle.addEventListener('change', () => {
            // console.log("Discount toggle changed:", discountToggle);
            updateFeeCalculations(form);
        });
    }

    const confirmBtn = form.querySelector('.confirm-payment-btn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', (e) => {
            e.preventDefault();
            // console.log("Confirm-payment-btn clicked for form:", form.id);
            openConfirmModal(form);
        });
    }
}

function openConfirmModal(form) {
    // console.log("openConfirmModal called for form:", form.id);
    // Recalculate totals
    const totals = updateFeeCalculations(form);
    // console.log("openConfirmModal Totals:", totals);
    
    // Update the modal's payable amount
    const modalPayableElement = document.getElementById('modalPayableAmount');
    // console.log("Modal Payable Element:", modalPayableElement);
    if (modalPayableElement) {
         modalPayableElement.textContent = `₹ ${totals.payable.toFixed(2)}`;
    }
    const modal = document.getElementById('confirmModal');
    if (modal) {
        // console.log("Opening modal confirmModal");
        modal.classList.remove('hidden');
    } else {
        // console.log("Modal confirmModal not found");
    }
}
