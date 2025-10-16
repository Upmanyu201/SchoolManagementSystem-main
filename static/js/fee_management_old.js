// D:\School-Management-System\School-Management-System-main\static\js\fee_management_old.js
// Complete optimized fee_management.js with all fixes
document.addEventListener('DOMContentLoaded', function () {
    // Initialize everything when page loads
    setupEventDelegation();
});

// Event delegation for dynamic elements
function setupEventDelegation() {
    // Handle View Fees buttons
    document.addEventListener('click', function (e) {
        const viewFeesBtn = e.target.closest('.view-fees-btn');
        if (viewFeesBtn) {
            e.preventDefault();
            handleViewFeesClick(viewFeesBtn);
        }

        // Handle discount toggle
        const discountToggle = e.target.closest('.discount-toggle');
        if (discountToggle) {
            const studentCard = discountToggle.closest('.student-card');
            const admissionNumber = studentCard?.querySelector('.view-fees-btn')?.dataset.admissionNumber;
            if (admissionNumber) {
                const feesContainer = document.querySelector(`#fees-container-${admissionNumber}`);
                if (feesContainer && !feesContainer.classList.contains('hidden')) {
                    // Reload fees with updated discount setting
                    studentCard.querySelector('.view-fees-btn').click();
                }
            }
        }
        if (e.target.matches('#payment_mode')) {
            const form = e.target.closest('form');
            const paymentFields = form?.querySelector('#cheque_fields');
            const paymentMode = e.target.value;

            if (paymentFields) {
                // Show/hide fields based on payment mode
                const isCash = paymentMode === 'Cash';
                paymentFields.classList.toggle('hidden', isCash);

                if (!isCash) {
                    // Update labels based on payment mode
                    const sourceLabel = paymentFields.querySelector('#payment_source_label');
                    const numberInput = paymentFields.querySelector('input[name="transaction_no"]');

                    if (sourceLabel && numberInput) {
                        switch (paymentMode) {
                            case 'Cheque':
                                sourceLabel.textContent = 'Bank Name';
                                numberInput.placeholder = 'Cheque number';
                                break;
                            case 'Online':
                                sourceLabel.textContent = 'Bank/Platform';
                                numberInput.placeholder = 'Transaction ID';
                                break;
                            case 'UPI':
                                sourceLabel.textContent = 'UPI App';
                                numberInput.placeholder = 'UPI Reference';
                                break;
                            case 'Card':
                                sourceLabel.textContent = 'Card Issuer';
                                numberInput.placeholder = 'Last 4 digits';
                                break;
                        }
                    }
                }
            }
        }
    });

    // Handle form submissions
    document.addEventListener('submit', function (e) {
        if (e.target.matches('[id^="depositForm-"]')) {
            e.preventDefault();
            handleFeeFormSubmit(e.target);
        }
    });

    // Handle discount inputs and payment mode changes
    document.addEventListener('input', function (e) {
        if (e.target.matches('.discount-input')) {
            validateDiscount(e.target);
            updateFeeCalculations(e.target.closest('form'));
        }
    });

    document.addEventListener('change', function (e) {
        if (e.target.matches('#payment_mode')) {
            const form = e.target.closest('form');
            const chequeFields = form?.querySelector('#cheque_fields');
            if (chequeFields) {
                chequeFields.classList.toggle('hidden', e.target.value !== 'Cheque');
            }
        }
    });
}

// View Fees button handler
function handleViewFeesClick(btn) {
    const studentCard = btn.closest('.student-card');
    const admissionNumber = btn.dataset.admissionNumber;
    const studentId = studentCard.dataset.studentId;
    const discountEnabled = studentCard.querySelector('.discount-toggle')?.checked || false;
    const feesContainer = document.querySelector(`#fees-container-${admissionNumber}`);


    // ✅ Toggle logic – अगर पहले से visible है तो hide कर दो
    if (!feesContainer.classList.contains('hidden')) {
        feesContainer.classList.add('hidden');
        btn.innerHTML = '📋 View Fees';
        return;
    }

    // ✅ Show loading and load data
    btn.innerHTML = '<span class="flex items-center"><span class="animate-spin mr-2">↻</span> Loading...</span>';
    btn.disabled = true;
    feesContainer.classList.remove('hidden');
    feesContainer.innerHTML = `
        <div class="border border-gray-200 rounded-lg p-4">
            <div class="flex justify-center">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
            <p class="text-center mt-2 text-gray-600">Loading fees data...</p>
        </div>
    `;

    // Fetch fees data
    fetch(`/student_fees/get_student_fees/?student_id=${studentId}&admission_number=${admissionNumber}&isDiscountEnabled=${discountEnabled}`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                feesContainer.innerHTML = data.html;
                initializeFeeForm(admissionNumber);
            } else {
                throw new Error(data.message || 'Error loading fees');
            }
        })
        .catch(error => {
            feesContainer.innerHTML = `
                <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
                    Error: ${error.message}
                </div>
            `;
            console.error('Error:', error);
        })
        .finally(() => {
            btn.innerHTML = '📋 View Fees';
            btn.disabled = false;
        });
}

// Initialize a fee form
function initializeFeeForm(admissionNumber) {
    const form = document.getElementById(`depositForm-${admissionNumber}`);
    if (!form) return;

    // Set default date if empty
    const dateInput = form.querySelector('input[type="date"]');
    if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }

    // Initialize payment mode handler
    const paymentModeSelect = form.querySelector('#payment_mode');
    if (paymentModeSelect) {
        // Trigger initial state
        paymentModeSelect.dispatchEvent(new Event('change'));
    }

    // Initialize fee checkboxes
    form.querySelectorAll('.fee-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', () => updateFeeCalculations(form));
    });

    // Initial calculation
    updateFeeCalculations(form);
}

// Update fee calculations
function updateFeeCalculations(form) {
    let totals = {
        amount: 0,
        discount: 0,
        payable: 0,
        selected: 0
    };

    form.querySelectorAll('.fee-row').forEach(row => {
        const checkbox = row.querySelector('.fee-checkbox');
        const amountCell = row.querySelector('.fee-amount');
        const discountInput = row.querySelector('.discount-input');
        const payableCell = row.querySelector('.payable-amount');

        if (!amountCell || !payableCell) return;

        const amount = parseFloat(amountCell.textContent.replace(/[^0-9.]/g, '')) || 0;
        const discount = discountInput ? parseFloat(discountInput.value) || 0 : 0;
        const payable = Math.max(0, amount - discount);

        if (checkbox?.checked) {
            totals.amount += amount;
            totals.discount += discount;
            totals.payable += payable;
            totals.selected++;

            payableCell.textContent = `₹ ${payable.toFixed(2)}`;
            payableCell.classList.remove('text-gray-400');
            payableCell.classList.add('text-green-600');
        } else {
            payableCell.textContent = '₹ 0.00';
            payableCell.classList.remove('text-green-600');
            payableCell.classList.add('text-gray-400');
        }

        // Update discount input max value if needed
        if (discountInput) {
            discountInput.max = amount;
            discountInput.min = 0;
        }
    });

    // Update summary
    updateSummaryDisplay(form, totals);

    // Update submit button
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = totals.selected === 0;
}

// Update summary display
function updateSummaryDisplay(form, { amount, discount, payable }) {
    const updateIfExists = (selector, value) => {
        const el = form.querySelector(selector);
        if (el) el.textContent = `₹ ${value.toFixed(2)}`;
    };

    updateIfExists('#total_selected', amount);
    updateIfExists('#total_discount', discount);
    updateIfExists('#total_payable', payable);
}

// Add these new functions at the bottom of fee_management.js
function showConfirmationModal(form, callback) {
    const modal = document.getElementById('confirmModal');
    const confirmBtn = document.getElementById('confirmPayment');
    const cancelBtn = document.getElementById('cancelPayment');
    const closeBtn = document.getElementById('closeModal');
    const payableAmount = form.querySelector('#total_payable')?.textContent || '₹0.00';

    // Update the modal with the payable amount
    const modalAmount = document.getElementById('modalPayableAmount');
    if (modalAmount) {
        modalAmount.textContent = payableAmount;
    }

    // Show modal
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // Prevent scrolling behind modal

    // Handle confirm button click
    const confirmHandler = () => {
        cleanup();
        callback();
    };

    // Handle cancel/close actions
    const cancelHandler = () => {
        cleanup();
        // Re-enable the submit button if needed
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
        }
    };

    // Cleanup event listeners and modal
    const cleanup = () => {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
        confirmBtn.removeEventListener('click', confirmHandler);
        cancelBtn.removeEventListener('click', cancelHandler);
        if (closeBtn) closeBtn.removeEventListener('click', cancelHandler);
    };

    // Add event listeners
    confirmBtn.addEventListener('click', confirmHandler);
    cancelBtn.addEventListener('click', cancelHandler);
    if (closeBtn) closeBtn.addEventListener('click', cancelHandler);

    // Close modal when clicking outside content
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            cancelHandler();
        }
    });
}

// Fee Handling
async function handleFeeFormSubmit(form) {
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalContent = submitBtn.innerHTML;
    const admissionNumber = form.id.replace('depositForm-', '');
    const studentId = form.querySelector('input[name="student_id"]')?.value;
    const paymentMode = form.querySelector('#payment_mode')?.value;
    const formData = new FormData(form);
    const depositDateInput = form.querySelector('input[name="deposit_date"]');
    const depositDateStr = depositDateInput ? depositDateInput.value : '';
    const cfCheckbox = form.querySelector('input[name="selected_fees"][value="carry_forward"]');
    const cfDiscountInput = form.querySelector('input[name="discount_carry_forward"]');
    const cfAmountInput = form.querySelector('input[name="amount_carry_forward"]');

    submitBtn.disabled = true;

    if (paymentMode !== 'Cash') {
        const chequeNo = form.querySelector('input[name="transaction_no"]')?.value;
        const bankName = form.querySelector('input[name="payment_source"]')?.value;

        if (!chequeNo || !bankName) {
            showFormError(form, 'If the mode of payment is not Cash, then it is mandatory to fill Tr/Cheque No and Bank Name.');
            return;
        }

        // formData.append('cheque_no', chequeNo);
        // formData.append('bank_name', bankName);
    }

    const selectedFees = form.querySelectorAll('input[name="selected_fees"]:checked, input[name="fee_ids"]:checked');
    if (selectedFees.length === 0) {
        showFormError(form, 'Please select at least one fee to pay');
        return;
    }

    if (cfCheckbox?.checked && cfDiscountInput && cfAmountInput) {
        const cfAmount = parseFloat(cfAmountInput.value || 0);
        const cfDiscount = parseFloat(cfDiscountInput.value || 0);
        if (cfDiscount > cfAmount) {
            throw new Error(`Carry Forward Discount ₹${cfDiscount} cannot be greater than the amount ₹${cfAmount}`);
        }
    }

    // Show confirmation modal
    showConfirmationModal(form, async () => {
        try {
            // Show loading state
            submitBtn.innerHTML = '<span class="flex items-center"><span class="animate-spin mr-2">↻</span> Processing...</span>';

            selectedFees.forEach(checkbox => {
                formData.append('selected_fees', checkbox.value);
            });

            // Validate form
            if (form.querySelectorAll('.fee-checkbox:checked').length === 0) {
                throw new Error('Please select at least one fee to pay');
            }

            // Create FormData and ensure required fields are included
            formData.append('admission_number', admissionNumber);
            if (studentId) formData.append('student_id', studentId);

            // Submit data
            const response = await fetch('/student_fees/submit_deposit/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (!response.ok || data.status !== 'success') {
                throw new Error(data.message || 'Payment failed');
            }

            // Success - redirect or show success message
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                window.location.reload();
            }
        } catch (error) {
            console.error('Submission error:', error);
            showFormError(form, error.message);
            submitBtn.innerHTML = originalContent;
            submitBtn.disabled = false;
        }
    });

    selectedFees.forEach(checkbox => {
        formData.append('selected_fees', checkbox.value);
    });
}

// Discount validation
function validateDiscount(input) {
    const maxDiscount = parseFloat(input.max) || 0;
    const currentValue = parseFloat(input.value) || 0;

    if (currentValue > maxDiscount) {
        input.value = maxDiscount;
        alert(`Discount cannot exceed ₹${maxDiscount}`);
    }
}

// Show form error
function showFormError(form, message) {
    const errorContainer = form.querySelector('#form-error-container');
    if (errorContainer) {
        errorContainer.innerHTML = `
            <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
                ${message}
            </div>
        `;
        errorContainer.classList.remove('hidden');
    } else {
        alert(message);
    }
}

// Get CSRF token
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

// In handleFeeFormSubmit function:
// const formData = new FormData(form);
// const selectedFees = form.querySelectorAll('.fee-checkbox:checked');

// if (selectedFees.length === 0) {
//     showFormError(form, 'Please select at least one fee to pay');
//     return;
// }

// // Ensure all selected fees are included
// selectedFees.forEach(checkbox => {
//     formData.append('selected_fees', checkbox.value);
// });
