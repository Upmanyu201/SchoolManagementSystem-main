// student_fees/static/student_fees/js/main.js
import { initializeFormHandlers, initializeFeeForm, handlePaymentModeChange } from './form_handlers.js';
import { initializeModals } from './modal_handlers.js';
import { updateFeeCalculations, updateAllRowDisplays } from './fee_calculations.js';

function initializeFeeManagement() {
    console.log("🚀 Initializing Fee Management");
    // Set up event listeners for view fees buttons
    document.querySelectorAll('.view-fees-btn').forEach(btn => {
        btn.addEventListener('click', handleViewFeesClick);
    });

    // Set up discount toggle handlers
    document.querySelectorAll('.discount-toggle').forEach(toggle => {
        toggle.addEventListener('change', handleDiscountToggle);
    });

    document.querySelectorAll('form[id^="depositForm-"]').forEach(form => initializeFeeForm(form));
}

async function handleViewFeesClick() {
    const studentId = this.dataset.studentId;
    const admissionNumber = this.dataset.admissionNumber;
    const container = document.getElementById(`fees-container-${admissionNumber}`);
    const discountEnabled = document.getElementById(`discount-toggle-${studentId}`).checked;

    // Show loading state
    container.classList.remove('hidden');
    this.disabled = true;

    try {
        const response = await fetch(`/student_fees/ajax/get-student-fees/?admission_number=${admissionNumber}&isDiscountEnabled=${discountEnabled}`);
        const data = await response.json();

        if (data.status === 'success') {
            container.innerHTML = data.html;

            // Initialize the fee form that was just loaded
            const form = container.querySelector('form');
            if (form) {
                // Initial calculation to set all values correctly
                updateFeeCalculations(form);

                // Set up payment mode handler
                const paymentMode = form.querySelector('#payment_mode');
                if (paymentMode) {
                    paymentMode.dispatchEvent(new Event('change'));
                }
                
                console.log('✅ Form initialized successfully');
                console.log('Form action:', form.action);
                console.log('Form method:', form.method);
                
                // Look for both submit button types
                const submitBtn = form.querySelector('button[type="submit"]') || form.querySelector('button[onclick*="showPaymentConfirmation"]');
                if (submitBtn) {
                    console.log('✅ Submit button found:', submitBtn.outerHTML.substring(0, 100));
                    console.log('✅ Button type:', submitBtn.type);
                    console.log('✅ Button onclick:', submitBtn.onclick);
                } else {
                    console.error('❌ Submit button not found in form');
                    console.log('🔍 Available buttons in form:', form.querySelectorAll('button').length);
                    form.querySelectorAll('button').forEach((btn, i) => {
                        console.log(`Button ${i}:`, btn.outerHTML.substring(0, 100));
                    });
                }
            }
        } else {
            alert(data.message);
            container.classList.add('hidden');
        }
    } catch (error) {
        console.error('Error:', error);
        container.classList.add('hidden');
    } finally {
        this.disabled = false;
    }
}

function handleDiscountToggle() {
    // console.log("handle Discount toggle loaded")
    const studentId = this.id.split('-')[2];
    const viewFeesBtn = document.querySelector(`.view-fees-btn[data-student-id="${studentId}"]`);
    if (viewFeesBtn && !document.getElementById(`fees-container-${viewFeesBtn.dataset.admissionNumber}`).classList.contains('hidden')) {
        viewFeesBtn.click();
    }
}

document.addEventListener('DOMContentLoaded', function () {
    initializeFeeManagement();
    initializeFormHandlers();
    initializeModals();
    setupFeeCalculationEvents(); // Add this new setup function
});

// Add this new function to handle all calculation-related events
function setupFeeCalculationEvents() {
    // Handle all fee-related input changes
    document.addEventListener('input', function (e) {
        if (e.target.matches('.discount-input')) {
            const form = e.target.closest('form');
            if (form) {
                // Validate discount doesn't exceed amount
                const row = e.target.closest('.fee-row');
                const amountCell = row?.querySelector('.fee-amount');
                if (amountCell) {
                    const maxDiscount = parseFloat(amountCell.textContent.replace(/[^0-9.]/g, '')) || 0;
                    const currentDiscount = parseFloat(e.target.value) || 0;
                    if (currentDiscount > maxDiscount) {
                        e.target.value = maxDiscount;
                    }
                }
                updateFeeCalculations(form);
            }
        }
    });

    // Handle checkbox changes
    document.addEventListener('change', function (e) {
        if (e.target.matches('.fee-checkbox')) {
            const form = e.target.closest('form');
            if (form) updateFeeCalculations(form);
        }

        // Handle payment mode changes
        if (e.target.matches('#payment_mode')) {
            handlePaymentModeChange(e.target);
        }
    });
}
// Add other functions as needed...