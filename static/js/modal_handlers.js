// student_fees/static/student_fees/js/modal_handlers.js

import { handleFeeFormSubmit } from './payment_handlers.js';
import { calculateFeeTotals } from './fee_calculations.js';

// console.log("modal_handlers.js loaded");

// Show confirmation modal
export function showConfirmationModal(form, callback) {
    // console.log("showConfirmationModal called for form:", form.id);
    const { amount, discount, payable } = calculateFeeTotals(form);
    // console.log("Calculated totals in modal:", { amount, discount, payable });

    const modal = document.getElementById('confirmModal');
    if (!modal) {
        // console.log("Modal confirmModal not found.");
        return;
    }

    const confirmBtn = document.getElementById('confirmPayment');
    const cancelBtn = document.getElementById('cancelPayment');
    const closeBtn = document.getElementById('closeModal');

    // ✅ Calculate actual payable amount (excluding carry forward)
    const calculateActualPayable = (form) => {
        let total = 0;
        form.querySelectorAll('.fee-checkbox:checked').forEach(checkbox => {
            const row = checkbox.closest('.fee-row');
            // Try to get the amount from the checkbox's dataset; if not available, use the text content from the fee-amount cell.
            let rawAmount = checkbox.dataset.amount;
            if (!rawAmount) {
                const amountCell = row.querySelector('.fee-amount');
                rawAmount = amountCell ? amountCell.textContent.replace(/[^0-9.]/g, '') : '0';
            }
            const amount = parseFloat(rawAmount) || 0;
            const discountInput = row.querySelector('.discount-input');
            const discount = parseFloat(discountInput?.value || '0');
            total += (amount - discount);
        });
        // console.log("calculateActualPayable result:", total);
        return '₹' + total.toFixed(2);
    };

    const payableAmount = calculateActualPayable(form);
    // console.log("Modal payableAmount calculated:", payableAmount);

    // ✅ Update modal content with actual payable
    const modalAmount = document.getElementById('modalPayableAmount');
    if (modalAmount) {
        modalAmount.textContent = payableAmount;
        // console.log("Updated modalPayableAmount to:", modalAmount.textContent);
    }

    // Show modal
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    // console.log("Modal displayed, body overflow set to hidden");

    // Event handlers
    const confirmHandler = () => {
        // console.log("Modal confirm button clicked");
        cleanup();
        callback();
    };

    const cancelHandler = () => {
        // console.log("Modal cancelling payment");
        cleanup();
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.disabled = false;
    };

    const cleanup = () => {
        // console.log("Cleaning up modal event listeners");
        modal.classList.add('hidden');
        document.body.style.overflow = '';
        confirmBtn?.removeEventListener('click', confirmHandler);
        cancelBtn?.removeEventListener('click', cancelHandler);
        closeBtn?.removeEventListener('click', cancelHandler);
        modal?.removeEventListener('click', outsideClickHandler);
    };

    const outsideClickHandler = (e) => {
        if (e.target === modal) cancelHandler();
    };

    // Add event listeners
    confirmBtn?.addEventListener('click', confirmHandler);
    cancelBtn?.addEventListener('click', cancelHandler);
    closeBtn?.addEventListener('click', cancelHandler);
    modal.addEventListener('click', outsideClickHandler);

    // console.log("Modal event listeners attached");
}


// Initialize modals
export function initializeModals() {
    // console.log("initializeModals called");
    // Close modal when clicking outside
    document.addEventListener('click', function(e) {
        const modal = document.getElementById('confirmModal');
        if (modal && !modal.classList.contains('hidden') && e.target === modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = '';
            // console.log("Modal closed on outside click");
        }
    });
}