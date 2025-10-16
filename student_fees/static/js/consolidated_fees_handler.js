// Consolidated Fees Handler - Merged functionality from all JS files
// Cache bust: v1.1

// Prevent duplicate class declaration
if (typeof ConsolidatedFeeManager !== 'undefined') {
    console.log('🔍 [FEES JS] ConsolidatedFeeManager already exists, skipping redefinition');
} else {

class ConsolidatedFeeManager {
    constructor() {
        this.apiEndpoints = {
            getStudentFees: '/student_fees/ajax/get-student-fees/',
            processPayment: '/student_fees/api/process-payment/'
        };
        this.currentForm = null;
        this.loadedStudents = new Set(); // Cache loaded students
        this.discountToggleTimeout = null;
        this.updateTimeout = null; // Debounce timeout for calculations
        this.init();
    }

    init() {
        this.setupCSRF();
        this.bindEvents();
    }

    setupCSRF() {
        // Get CSRF token from multiple sources
        this.csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                        document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || 
                        document.querySelector('input[name=csrfmiddlewaretoken]')?.value ||
                        '';
        
        console.log('🔍 [FEES JS] CSRF token found:', this.csrfToken ? 'Yes' : 'No');
    }

    bindEvents() {
        // Remove global click handler to prevent conflicts
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('discount-toggle')) {
                this.handleDiscountToggle(e);
            }
        });
    }

    async handleViewFeesClick(e, studentId, admissionNumber, buttonText) {
        // Handle both event-based and direct calls
        let button;
        if (e && e.target) {
            // Called from event listener
            if (e.preventDefault) e.preventDefault();
            if (e.stopPropagation) e.stopPropagation();
            button = e.target.classList.contains('view-fees-btn') ? e.target : e.target.closest('.view-fees-btn');
            studentId = button.getAttribute('data-student-id');
            admissionNumber = button.getAttribute('data-admission-number');
            buttonText = button.textContent.trim();
        } else {
            // Called directly from template (e is actually studentId)
            if (typeof e === 'string') {
                studentId = e;
                admissionNumber = studentId;
                buttonText = admissionNumber;
            }
            // Find button by data attributes
            button = document.querySelector(`[data-student-id="${studentId}"]`) || 
                    document.querySelector(`[data-admission-number="${admissionNumber}"]`);
        }
        
        console.log('🔍 [FEES JS] handleViewFeesClick called', {
            studentId,
            admissionNumber,
            buttonText,
            buttonElement: button,
            clickedElement: e?.target
        });
        
        if (!studentId || !admissionNumber) {
            console.error('❌ [FEES JS] Missing student data', { studentId, admissionNumber });
            this.showMessage('Missing student data', 'error');
            return;
        }

        // CRITICAL FIX: Always find container within the clicked button's student card
        const studentCard = button.closest('.student-card');
        let container = null;
        
        if (studentCard) {
            // Find container within this specific student card
            container = studentCard.querySelector(`#fees-container-${admissionNumber}`);
            
            // Fallback: any container within this card
            if (!container) {
                container = studentCard.querySelector('[id^="fees-container-"]');
            }
        }
        
        // Last resort: global lookup
        if (!container) {
            container = document.getElementById('fees-container-' + admissionNumber);
        }
        
        console.log('🔍 [FEES JS] Container lookup', {
            admissionNumber: admissionNumber,
            expectedId: 'fees-container-' + admissionNumber,
            containerFound: !!container,
            containerId: container?.id,
            allContainers: Array.from(document.querySelectorAll('[id^="fees-container-"]')).map(c => c.id)
        });
        
        if (!container) {
            console.error('❌ [FEES JS] Container not found', {
                expectedId: 'fees-container-' + admissionNumber,
                availableContainers: Array.from(document.querySelectorAll('[id^="fees-container-"]')).map(c => c.id)
            });
            this.showMessage('Fees container not found for student ' + admissionNumber, 'error');
            return;
        }
        
        // Verify container belongs to correct student
        const containerAdmissionNumber = container.id.replace('fees-container-', '');
        if (containerAdmissionNumber !== admissionNumber) {
            console.error('❌ [FEES JS] Container mismatch!', {
                buttonAdmission: admissionNumber,
                containerAdmission: containerAdmissionNumber,
                containerId: container.id
            });
            this.showMessage('Container mismatch detected', 'error');
            return;
        }

        // Prevent rapid clicking during state transitions
        if (button.dataset.processing === 'true') {
            console.log('🚫 [FEES JS] Button processing, ignoring click');
            return;
        }
        
        console.log('🔍 [FEES JS] Final container validation', {
            studentId: studentId,
            admissionNumber: admissionNumber,
            containerId: container.id,
            containerMatch: container.id === 'fees-container-' + admissionNumber
        });
        
        // Use data attribute as single source of truth for state
        const isExpanded = container.dataset.expanded === 'true';
        
        console.log('🔍 [FEES JS] Container state check', {
            isExpanded,
            dataExpanded: container.dataset.expanded,
            hasHiddenClass: container.classList.contains('hidden'),
            displayStyle: container.style.display
        });
        
        if (!isExpanded) {
            console.log('🔍 [FEES JS] Expanding container (loading fees)');
            await this.loadStudentFees(studentId, admissionNumber, button, container);
        } else {
            console.log('🔍 [FEES JS] Collapsing container (hiding fees)');
            this.hideFeesContainer(button, container);
        }
    }

    async loadStudentFeesDirectly(studentId, admissionNumber, button, container) {
        return this.loadStudentFees(studentId, admissionNumber, button, container);
    }

    async loadStudentFees(studentId, admissionNumber, button, container) {
        console.log('🔍 [AJAX] Starting request for:', admissionNumber, 'Container:', container.id);
        
        // Prevent duplicate AJAX calls
        const cacheKey = `${admissionNumber}_${Date.now()}`;
        if (this.loadedStudents.has(admissionNumber)) {
            console.log('🔍 [FEES JS] Student already loaded, skipping duplicate request');
            return;
        }
        
        try {
            // Set processing state to prevent rapid clicks
            button.dataset.processing = 'true';
            this.loadedStudents.add(admissionNumber);
            this.updateButtonState(button, 'loading');
            
            // Set container to expanded state
            container.dataset.expanded = 'true';
            container.classList.remove('hidden');
            container.style.display = 'block';
            container.innerHTML = this.getLoadingHTML();

            const studentCard = button.closest('.student-card');
            const discountToggle = studentCard.querySelector('.discount-toggle');
            const isDiscountEnabled = discountToggle ? discountToggle.checked : false;
            
            console.log('🔍 [FEES JS] Request parameters', {
                studentId,
                admissionNumber,
                isDiscountEnabled,
                containerId: container.id,
                url: `/student_fees/ajax/get-student-fees/?admission_number=${encodeURIComponent(admissionNumber)}&discount_enabled=${isDiscountEnabled}`
            });

            // Fetch the fees_rows.html template with student data
            const requestUrl = `/student_fees/ajax/get-student-fees/?admission_number=${encodeURIComponent(admissionNumber)}&discount_enabled=${isDiscountEnabled}`;
            console.log('🚀 [AJAX] Requesting:', admissionNumber, 'URL:', requestUrl);
            
            const response = await fetch(requestUrl, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/html, */*'
                }
            });
            
            console.log('🔍 [AJAX] Response headers:', {
                contentType: response.headers.get('content-type'),
                status: response.status,
                statusText: response.statusText
            });
            
            console.log('🔍 [FEES JS] Response received', {
                status: response.status,
                statusText: response.statusText,
                ok: response.ok
            });

            if (!response.ok) {
                console.error('❌ [FEES JS] HTTP error', {
                    status: response.status,
                    statusText: response.statusText
                });
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('✅ [FEES JS] Data parsed', {
                status: data.status,
                feesCount: data.fees_count,
                htmlLength: data.html ? data.html.length : 0
            });
            
            if (data.status === 'success') {
                // CRITICAL: Re-verify container is within correct student card
                const studentCard = button.closest('.student-card');
                const cardContainer = studentCard?.querySelector(`#fees-container-${admissionNumber}`);
                
                if (!cardContainer || cardContainer !== container) {
                    console.error('❌ [FEES JS] CRITICAL: Container not in correct student card!', {
                        originalContainer: container.id,
                        cardContainer: cardContainer?.id,
                        admissionNumber: admissionNumber
                    });
                    return;
                }
                
                console.log('✅ [AJAX] Success for:', admissionNumber, 'HTML length:', data.html.length);
                container.innerHTML = data.html;
                this.initializeFeesForm(admissionNumber);
                this.updateButtonState(button, 'close');
                console.log('✅ [FEES JS] Fee form initialized successfully for', admissionNumber);
                
                // Ensure container is visible and expanded
                container.classList.remove('hidden');
                container.style.display = 'block';
                container.dataset.expanded = 'true';
                
                // Clear processing state
                button.dataset.processing = 'false';
                
                // Remove from cache after successful load
                setTimeout(() => {
                    this.loadedStudents.delete(admissionNumber);
                }, 2000);
            } else {
                console.error('❌ [FEES JS] Error response', data.message);
                container.innerHTML = this.getErrorHTML(data.message || 'Error loading fees');
                button.dataset.processing = 'false';
            }

        } catch (error) {
            console.error('❌ [FEES JS] Exception in loadStudentFees', {
                error: error.message,
                stack: error.stack,
                admissionNumber: admissionNumber,
                studentId: studentId,
                containerId: container?.id,
                requestUrl: `/student_fees/ajax/get-student-fees/?admission_number=${encodeURIComponent(admissionNumber)}`
            });
            
            // Show detailed error in container
            const errorHtml = this.getErrorHTML(`Failed to load fees: ${error.message}`);
            console.log('🔍 [FEES JS] Setting error HTML', {
                errorHtml: errorHtml.substring(0, 200),
                containerId: container?.id
            });
            
            container.innerHTML = errorHtml;
            // Clear processing state and remove from cache on error
            button.dataset.processing = 'false';
            this.loadedStudents.delete(admissionNumber);
        }
    }

    hideFeesContainer(button, container) {
        console.log('🔍 [FEES JS] hideFeesContainer called');
        
        // Set processing state to prevent rapid clicks
        button.dataset.processing = 'true';
        
        // Hide container with animation
        container.style.transition = 'opacity 0.3s ease';
        container.style.opacity = '0';
        
        setTimeout(() => {
            container.classList.add('hidden');
            container.style.display = 'none';
            container.style.opacity = '';
            container.style.transition = '';
            container.dataset.expanded = 'false';
            
            // Clear processing state after animation
            button.dataset.processing = 'false';
        }, 300);
        
        this.updateButtonState(button, 'process');
        
        // Clear cache when hiding
        const admissionNumber = button.getAttribute('data-admission-number');
        if (admissionNumber) {
            this.loadedStudents.delete(admissionNumber);
        }
        
        console.log('✅ [FEES JS] Container hidden successfully');
    }

    updateButtonState(button, state) {
        const states = {
            process: {
                text: '<i class="fas fa-money-check-alt mr-2"></i>Process Payment',
                classes: 'from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700'
            },
            loading: {
                text: '<i class="fas fa-spinner fa-spin mr-2"></i>Loading...',
                classes: 'from-blue-500 to-blue-600'
            },
            close: {
                text: '<i class="fas fa-times mr-2"></i>Close Payment',
                classes: 'from-red-500 to-red-600 hover:from-red-600 hover:to-red-700'
            }
        };

        const config = states[state];
        if (config) {
            button.innerHTML = config.text;
            button.className = button.className.replace(/from-\w+-\d+|to-\w+-\d+|hover:from-\w+-\d+|hover:to-\w+-\d+/g, '');
            button.className += ' ' + config.classes;
        }
    }

    renderFeesForm(data, discountEnabled) {
        const { student, payable_fees } = data;
        
        if (!payable_fees || payable_fees.length === 0) {
            return `
                <div class="bg-green-50 border-2 border-green-200 rounded-xl p-8 text-center">
                    <i class="fas fa-check-circle text-green-500 text-4xl mb-4"></i>
                    <h3 class="text-xl font-bold text-green-800 mb-2">All Fees Paid!</h3>
                    <p class="text-green-600">This student has no pending fees.</p>
                </div>
            `;
        }

        return `
            <div class="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
                <form id="depositForm-${student.admission_number}" action="${this.apiEndpoints.processPayment}" method="POST" class="space-y-6">
                    <input type="hidden" name="csrfmiddlewaretoken" value="${this.csrfToken}">
                    <input type="hidden" name="student_id" value="${student.id}">
                    
                    <div class="bg-white rounded-xl shadow-lg overflow-hidden">
                        <div class="bg-gradient-to-r from-blue-500 to-indigo-600 p-4">
                            <h3 class="text-white font-bold text-lg flex items-center">
                                <i class="fas fa-list-alt mr-2"></i>Payable Fees
                            </h3>
                        </div>
                        
                        <div class="overflow-x-auto">
                            <table class="w-full">
                                <thead class="bg-gray-50">
                                    <tr>
                                        <th class="px-4 py-3 text-left">Select</th>
                                        <th class="px-4 py-3 text-left">Fee Type</th>
                                        <th class="px-4 py-3 text-right">Amount</th>
                                        ${discountEnabled ? '<th class="px-4 py-3 text-right">Discount</th>' : ''}
                                        <th class="px-4 py-3 text-right">Payable</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${payable_fees.map(fee => this.renderFeeRow(fee, discountEnabled)).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <div class="bg-white rounded-xl p-6 shadow-lg">
                        <h4 class="font-bold text-lg mb-4 flex items-center">
                            <i class="fas fa-calculator mr-2 text-blue-500"></i>Payment Summary
                        </h4>
                        <div class="grid grid-cols-3 gap-4 text-center">
                            <div class="bg-blue-50 rounded-lg p-4">
                                <div class="text-sm text-gray-600">Total Selected</div>
                                <div id="total_selected" class="text-xl font-bold text-blue-600">₹ 0.00</div>
                            </div>
                            <div class="bg-green-50 rounded-lg p-4">
                                <div class="text-sm text-gray-600">Total Discount</div>
                                <div id="total_discount" class="text-xl font-bold text-green-600">₹ 0.00</div>
                            </div>
                            <div class="bg-purple-50 rounded-lg p-4">
                                <div class="text-sm text-gray-600">Total Payable</div>
                                <div id="total_payable" class="text-xl font-bold text-purple-600">₹ 0.00</div>
                            </div>
                        </div>
                    </div>

                    ${this.renderPaymentDetailsForm()}

                    <div class="text-center">
                        <button type="submit" class="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold py-4 px-8 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg">
                            <i class="fas fa-credit-card mr-2"></i>Process Payment
                        </button>
                    </div>
                </form>
            </div>
        `;
    }

    renderFeeRow(fee, discountEnabled) {
        const isOverdue = fee.is_overdue ? 'bg-red-50 border-l-4 border-red-400' : '';
        const overdueIcon = fee.is_overdue ? '<i class="fas fa-exclamation-triangle text-red-500 mr-1"></i>' : '';
        
        // DYNAMIC: Calculate remaining balance and payable amount
        const paidAmount = fee.paid_amount || 0;
        const discountPaid = fee.discount_paid || 0;
        const remainingBalance = fee.amount - (paidAmount + discountPaid);
        const maxPayable = Math.max(0, remainingBalance);
        const currentPayable = fee.payable || maxPayable;
        const dueAmount = Math.max(0, maxPayable - currentPayable);
        
        return `
            <tr class="fee-row border-b hover:bg-gray-50 ${isOverdue}"
                data-paid-amount="${paidAmount}"
                data-discount-paid="${discountPaid}">
                <td class="px-4 py-3">
                    <input type="checkbox" class="fee-checkbox form-checkbox h-5 w-5 text-blue-600" 
                           name="selected_fees" value="${fee.id}" 
                           data-amount="${fee.amount}"
                           data-paid-amount="${paidAmount}"
                           data-discount-paid="${discountPaid}">
                </td>
                <td class="px-4 py-3">
                    <div class="font-medium">${overdueIcon}${fee.display_name}</div>
                    ${fee.due_date ? `<div class="text-sm text-red-600">Due: ${fee.due_date}</div>` : ''}
                </td>
                <td class="px-4 py-3 text-right">
                    <span class="fee-amount font-semibold">₹ ${fee.amount.toFixed(2)}</span>
                    <input type="hidden" name="original_amount_${fee.id}" value="${fee.amount}">
                    <input type="hidden" name="paid_amount_${fee.id}" value="${paidAmount}">
                    <input type="hidden" name="discount_paid_${fee.id}" value="${discountPaid}">
                </td>
                ${discountEnabled ? `
                    <td class="px-4 py-3 text-right">
                        <input type="number" class="discount-input w-20 px-2 py-1 border rounded text-right" 
                               name="discount_${fee.id}" min="0" max="${maxPayable}" step="0.01" value="0">
                    </td>
                ` : ''}
                <td class="px-4 py-3 text-right">
                    <input type="number" class="payable-input w-24 px-2 py-1 border-2 border-green-300 rounded text-right font-bold text-green-600" 
                           name="payable_${fee.id}" min="0.01" max="${maxPayable}" step="0.01" value="${currentPayable.toFixed(2)}">
                </td>
                <td class="px-4 py-3 text-right">
                    <span class="due-amount font-bold text-red-600">₹ ${dueAmount.toFixed(2)}</span>
                    <input type="hidden" name="due_${fee.id}" value="${dueAmount}">
                </td>
            </tr>
        `;
    }

    renderPaymentDetailsForm() {
        return `
            <div class="bg-white rounded-xl p-6 shadow-lg">
                <h4 class="font-bold text-lg mb-4 flex items-center">
                    <i class="fas fa-credit-card mr-2 text-blue-500"></i>Payment Details
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Payment Method *</label>
                        <select id="payment_mode" name="payment_mode" class="w-full px-3 py-2 border border-gray-300 rounded-lg" required>
                            <option value="Cash">Cash</option>
                            <option value="Online">Online Transfer</option>
                            <option value="UPI">UPI</option>
                            <option value="Cheque">Cheque</option>
                            <option value="Card">Card</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Payment Date *</label>
                        <input type="datetime-local" id="deposit_date" name="deposit_date" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-lg" required>
                    </div>
                </div>
                
                <div id="extra_fields" class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4" style="display: none;">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Transaction Number</label>
                        <input type="text" id="trans_no" name="transaction_no" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                    </div>
                    <div>
                        <label id="source_label" class="block text-sm font-medium text-gray-700 mb-2">Payment Source</label>
                        <input type="text" id="pay_source" name="payment_source" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                    </div>
                </div>
            </div>
        `;
    }

    initializeFeesForm(admissionNumber) {
        console.log('🔍 [FEES JS] initializeFeesForm called for admission:', admissionNumber);
        const form = document.getElementById('depositForm-' + admissionNumber);
        if (!form) {
            console.error('❌ [FEES JS] Form not found:', 'depositForm-' + admissionNumber);
            console.log('🔍 [FEES JS] Available forms:', Array.from(document.querySelectorAll('form[id^="depositForm-"]')).map(f => f.id));
            return;
        }
        console.log('✅ [FEES JS] Form found, initializing for admission:', admissionNumber, 'Form ID:', form.id);

        // Set current date and time
        const now = new Date();
        const depositDateInput = form.querySelector('#deposit_date');
        if (depositDateInput) {
            depositDateInput.value = now.toISOString().slice(0, 16);
        }

        // Payment method change handler
        const paymentModeSelect = form.querySelector('#payment_mode');
        const extraFields = form.querySelector('#extra_fields');
        
        if (paymentModeSelect && extraFields) {
            paymentModeSelect.addEventListener('change', () => {
                this.togglePaymentFields(paymentModeSelect.value, extraFields, form);
            });
        }

        // Fee selection and calculation handlers
        const checkboxes = form.querySelectorAll('.fee-checkbox');
        const discountInputs = form.querySelectorAll('.discount-input');
        
        console.log('🔍 [FEES JS] Adding event listeners', {
            checkboxes: checkboxes.length,
            discountInputs: discountInputs.length
        });
        
        checkboxes.forEach((checkbox, index) => {
            checkbox.addEventListener('change', () => {
                console.log('🔍 [FEES JS] Checkbox changed', {
                    index,
                    checked: checkbox.checked,
                    value: checkbox.value,
                    amount: checkbox.dataset.amount
                });
                
                // Immediate visual feedback
                const row = checkbox.closest('tr');
                if (checkbox.checked) {
                    row.classList.add('bg-green-50', 'border-green-200');
                } else {
                    row.classList.remove('bg-green-50', 'border-green-200');
                }
                
                // Update totals with slight delay to prevent rapid calculations
                clearTimeout(this.updateTimeout);
                this.updateTimeout = setTimeout(() => {
                    this.updateTotals(form);
                }, 100);
            });
        });

        discountInputs.forEach((input, index) => {
            input.addEventListener('input', () => {
                console.log('🔍 [FEES JS] Discount input changed', {
                    index,
                    value: input.value
                });
                
                // Validate discount doesn't exceed amount
                const row = input.closest('tr');
                const checkbox = row.querySelector('.fee-checkbox');
                const maxAmount = parseFloat(checkbox.dataset.amount || 0);
                const discountValue = parseFloat(input.value || 0);
                
                if (discountValue > maxAmount) {
                    input.value = maxAmount.toFixed(2);
                    alert(`Discount cannot exceed fee amount of ₹${maxAmount.toFixed(2)}`);
                }
                
                // Update totals with debouncing
                clearTimeout(this.updateTimeout);
                this.updateTimeout = setTimeout(() => {
                    this.updateTotals(form);
                }, 300);
            });
        });

        // ✅ FIX: Payable input change handler (will be added dynamically by AtomicFeeCalculator)
        // Event delegation for dynamically created payable inputs
        form.addEventListener('input', (e) => {
            if (e.target.name && e.target.name.includes('payable_')) {
                console.log('🔍 [FEES JS] Payable input changed', {
                    name: e.target.name,
                    value: e.target.value
                });
                
                clearTimeout(this.updateTimeout);
                this.updateTimeout = setTimeout(() => {
                    this.updateTotals(form);
                }, 300);
            }
        });

        // Form submission
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            console.log('🔍 [FEES JS] Form submission triggered');
            this.handleFormSubmission(form);
        });
        
        // Payment button handler - multiple selectors for compatibility
        let paymentBtn = form.querySelector('button[type="submit"]');
        if (!paymentBtn) paymentBtn = form.querySelector('.payment-btn');
        if (!paymentBtn) paymentBtn = form.querySelector('#confirmPaymentBtn');
        if (!paymentBtn) paymentBtn = form.querySelector('button');
        
        if (paymentBtn) {
            paymentBtn.addEventListener('click', (e) => {
                e.preventDefault();
                
                console.log('🔍 [FEES JS] Payment button clicked');
                
                const selectedFees = form.querySelectorAll('.fee-checkbox:checked');
                if (selectedFees.length === 0) {
                    alert('Please select at least one fee to pay.');
                    return;
                }
                
                this.updateTotals(form);
                
                // Show confirmation modal
                const modal = document.getElementById('paymentModal');
                if (modal) {
                    this.showPaymentModal(form, modal);
                } else {
                    form.submit();
                }
            });
        } else {
            // Fallback: form submit handler
            form.addEventListener('submit', (e) => {
                const selectedFees = form.querySelectorAll('.fee-checkbox:checked');
                if (selectedFees.length === 0) {
                    e.preventDefault();
                    alert('Please select at least one fee to pay.');
                }
            });
        }

        // Initialize totals
        console.log('🔍 [FEES JS] Initializing totals calculation');
        this.updateTotals(form);
        
        // Set default payment date
        const paymentDateInput = form.querySelector('#deposit_date');
        if (paymentDateInput) {
            paymentDateInput.value = new Date().toISOString().slice(0, 16);
        }
        
        console.log('✅ [FEES JS] Form initialization completed');
    }



    /**
     * DYNAMIC fallback calculation method if AtomicFeeCalculator is not available
     */
    fallbackUpdateTotals(form) {
        console.log('🔍 [FEES JS] Using DYNAMIC fallback calculation method');
        
        const selectedFees = form.querySelectorAll('.fee-checkbox:checked');
        let totalOriginal = 0;
        let totalDiscount = 0;
        let totalPayable = 0;
        let totalDue = 0;
        
        selectedFees.forEach(checkbox => {
            const row = checkbox.closest('tr');
            const originalAmount = parseFloat(checkbox.dataset.amount || 0);
            const paidAmount = parseFloat(checkbox.dataset.paidAmount || 0);
            const discountPaid = parseFloat(row.dataset.discountPaid || 0);
            
            const discountInput = row.querySelector('.discount-input');
            const currentDiscount = discountInput ? parseFloat(discountInput.value || 0) : 0;
            
            const payableInput = row.querySelector('.payable-input');
            
            // DYNAMIC: Calculate remaining balance after previous payments
            const remainingBalance = originalAmount - (paidAmount + discountPaid);
            const maxPayable = Math.max(0, remainingBalance);
            
            // DYNAMIC: Get current payable amount (user input or max)
            const currentPayable = payableInput ? parseFloat(payableInput.value || maxPayable) : maxPayable;
            const payable = Math.min(currentPayable, maxPayable);
            
            // DYNAMIC: Due = Remaining balance after current payment
            const due = Math.max(0, maxPayable - payable);
            
            totalOriginal += originalAmount;
            totalDiscount += currentDiscount;
            totalPayable += payable;
            totalDue += due;
        });
        
        // Update totals display
        this.updateElement('total_selected', `₹ ${totalOriginal.toFixed(2)}`);
        this.updateElement('total-original', `₹ ${totalOriginal.toFixed(2)}`);
        this.updateElement('total_discount', `₹ ${totalDiscount.toFixed(2)}`);
        this.updateElement('total-discount', `₹ ${totalDiscount.toFixed(2)}`);
        this.updateElement('total_payable', `₹ ${totalPayable.toFixed(2)}`);
        this.updateElement('total-payable', `₹ ${totalPayable.toFixed(2)}`);
        this.updateElement('total_due', `₹ ${totalDue.toFixed(2)}`);
        this.updateElement('total-due', `₹ ${totalDue.toFixed(2)}`);
        this.updateElement('final-amount', `₹ ${totalDue.toFixed(2)}`);
        
        console.log('✅ [FEES JS] DYNAMIC fallback totals updated', {
            totalOriginal, totalDiscount, totalPayable, totalDue
        });
    }

    /**
     * Helper to update element text content
     */
    updateElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    togglePaymentFields(mode, extraFields, form) {
        const sourceLabel = form.querySelector('#source_label');
        const transInput = form.querySelector('#trans_no');
        const sourceInput = form.querySelector('#pay_source');

        if (mode === 'Cash') {
            extraFields.style.display = 'none';
        } else {
            extraFields.style.display = 'grid';
            
            const configs = {
                'Cheque': { label: 'Bank Name', transPlaceholder: 'Cheque Number', sourcePlaceholder: 'Enter bank name' },
                'UPI': { label: 'UPI App', transPlaceholder: 'UPI Reference', sourcePlaceholder: 'Enter UPI app' },
                'Online': { label: 'Bank/Platform', transPlaceholder: 'Transaction ID', sourcePlaceholder: 'Enter platform' },
                'Card': { label: 'Card Issuer', transPlaceholder: 'Last 4 digits', sourcePlaceholder: 'Enter issuer' }
            };

            const config = configs[mode] || configs['Online'];
            if (sourceLabel) sourceLabel.textContent = config.label;
            if (transInput) transInput.placeholder = config.transPlaceholder;
            if (sourceInput) sourceInput.placeholder = config.sourcePlaceholder;
        }
    }

    updateTotals(form) {
        console.log('🔍 [FEES JS] updateTotals called - delegating to AtomicFeeCalculator');
        
        if (!window.atomicFeeCalculator) {
            console.error('❌ [FEES JS] AtomicFeeCalculator not available');
            this.fallbackUpdateTotals(form);
            return;
        }
        
        const feeData = this.getFeeDataFromForm(form);
        window.atomicFeeCalculator.updateFeeDisplay(form.id, feeData);
        
        console.log('✅ [FEES JS] Delegated to AtomicFeeCalculator');
    }

    async handleFormSubmission(form) {
        console.log('🔍 [FEES JS] handleFormSubmission started');
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        
        try {
            const selectedFees = form.querySelectorAll('.fee-checkbox:checked');
            console.log('🔍 [FEES JS] Selected fees count:', selectedFees.length);
            
            if (selectedFees.length === 0) {
                console.warn('⚠️ [FEES JS] No fees selected');
                this.showMessage('Please select at least one fee to pay.', 'error');
                return;
            }

            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
            submitBtn.disabled = true;

            const formData = new FormData(form);
            const paymentData = {
                student_id: formData.get('student_id'),
                selected_fees: [],
                payment_mode: formData.get('payment_mode'),
                transaction_no: formData.get('transaction_no') || '',
                payment_source: formData.get('payment_source') || ''
            };

            selectedFees.forEach(checkbox => {
                const feeId = checkbox.value;
                const amount = formData.get(`amount_${feeId}`) || '0';
                const discount = formData.get(`discount_${feeId}`) || '0';

                paymentData.selected_fees.push({
                    id: feeId,
                    amount: parseFloat(amount),
                    discount: parseFloat(discount)
                });
            });

            console.log('🔍 [FEES JS] Sending payment request', {
                url: this.apiEndpoints.processPayment,
                paymentData
            });
            
            const response = await fetch(this.apiEndpoints.processPayment, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(paymentData)
            });

            console.log('🔍 [FEES JS] Payment response received', {
                status: response.status,
                ok: response.ok
            });
            
            const result = await response.json();
            console.log('🔍 [FEES JS] Payment result', result);

            if (result.status === 'success') {
                this.showMessage(result.message, 'success');
                
                // Notify other tabs/windows about payment completion
                try {
                    localStorage.setItem('payment_completed', Date.now().toString());
                } catch (e) {
                    console.log('LocalStorage not available');
                }
                
                // Trigger dashboard refresh if available
                try {
                    if (typeof window.refreshDashboard === 'function') {
                        window.refreshDashboard();
                    }
                } catch (e) {
                    console.log('Dashboard refresh not available');
                }
                
                // Fast redirect with smooth transition
                setTimeout(() => {
                    document.body.style.opacity = '0.8';
                    document.body.style.transition = 'opacity 0.3s ease';
                    window.location.href = `/student_fees/payment/${paymentData.student_id}/?receipt_no=${result.data.receipt_no}`;
                }, 800);
            } else {
                this.showMessage(result.message || 'Payment failed', 'error');
            }

        } catch (error) {
            console.error('❌ [FEES JS] Payment submission error', {
                error: error.message,
                stack: error.stack
            });
            this.showMessage('Network error: ' + error.message, 'error');
        } finally {
            if (submitBtn) {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }
            console.log('✅ [FEES JS] Form submission completed');
        }
    }

    handleDiscountToggle(e) {
        const studentCard = e.target.closest('.student-card');
        const admissionNumber = studentCard.querySelector('.view-fees-btn').getAttribute('data-admission-number');
        
        const container = document.getElementById('fees-container-' + admissionNumber);
        if (container && !container.classList.contains('hidden')) {
            // Add a small delay to prevent rapid toggling
            clearTimeout(this.discountToggleTimeout);
            this.discountToggleTimeout = setTimeout(() => {
                const button = studentCard.querySelector('.view-fees-btn');
                const studentId = studentCard.getAttribute('data-student-id');
                this.loadStudentFees(studentId, admissionNumber, button, container);
            }, 300); // 300ms delay
        }
    }

    getLoadingHTML() {
        return `
            <div class="border-2 border-dashed border-blue-300 rounded-xl p-8 text-center">
                <div class="flex justify-center mb-4">
                    <div class="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
                </div>
                <p class="text-lg font-semibold text-gray-700">Loading fees data...</p>
            </div>
        `;
    }

    getErrorHTML(message) {
        const errorHtml = `
            <div class="bg-red-50 border-2 border-red-200 rounded-xl p-6 text-center">
                <i class="fas fa-exclamation-triangle text-red-500 text-3xl mb-3"></i>
                <p class="text-red-700 font-semibold">${message}</p>
                <div class="mt-4 text-sm text-red-600">
                    <p>Debug Info: ${new Date().toISOString()}</p>
                    <p>Check browser console for detailed logs</p>
                </div>
            </div>
        `;
        
        console.log('🔍 [FEES JS] Generated error HTML', {
            message: message,
            htmlLength: errorHtml.length
        });
        
        return errorHtml;
    }

    showPaymentModal(form, modal) {
        console.log('🔍 [FEES JS] Showing payment modal');
        
        // CRITICAL FIX: Position modal within correct student card
        const studentCard = form.closest('.student-card');
        if (!studentCard) {
            console.error('❌ [FEES JS] Student card not found');
            return;
        }
        
        // Create overlay for student card
        let overlay = studentCard.querySelector('.modal-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'modal-overlay';
            overlay.style.position = 'absolute';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.right = '0';
            overlay.style.bottom = '0';
            overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
            overlay.style.zIndex = '40';
            studentCard.style.position = 'relative';
            studentCard.appendChild(overlay);
        }
        
        // Move modal to correct student card
        studentCard.appendChild(modal);
        
        // Clear modal data first
        this.clearModalData(modal);
        
        // Get current student info from form
        const studentId = form.querySelector('input[name="student_id"]').value;
        const formId = form.id;
        const admissionNumber = formId.replace('depositForm-', '');
        
        console.log('🔍 [FEES JS] Modal for student:', { studentId, admissionNumber, formId });
        
        // Get student name from card
        const studentName = studentCard.querySelector('h3')?.textContent?.trim() || 'Unknown Student';
        const modalStudentName = modal.querySelector('.font-semibold');
        const modalAdmissionNo = modal.querySelectorAll('.font-semibold')[1];
        
        if (modalStudentName) modalStudentName.textContent = studentName;
        if (modalAdmissionNo) modalAdmissionNo.textContent = admissionNumber;
        
        const selectedFees = form.querySelectorAll('.fee-checkbox:checked');
        const paymentMethod = form.querySelector('#payment_mode').value;
        
        // Update payment details
        const modalPaymentMethod = modal.querySelector('#modalPaymentMethod');
        const modalPaymentDate = modal.querySelector('#modalPaymentDate');
        const paymentDateInput = form.querySelector('#deposit_date');
        
        if (modalPaymentMethod) modalPaymentMethod.textContent = paymentMethod;
        if (modalPaymentDate && paymentDateInput) {
            const dateValue = paymentDateInput.value;
            if (dateValue) {
                const formattedDate = new Date(dateValue).toLocaleString();
                modalPaymentDate.textContent = formattedDate;
            }
        }
        
        // Update fee list and calculate totals
        const feesList = modal.querySelector('#modalFeesList');
        if (feesList) {
            feesList.innerHTML = '';
            
            let totalOriginal = 0;
            let totalDiscount = 0;
            let totalPayable = 0;
            let totalDue = 0;
            
            selectedFees.forEach(checkbox => {
                const row = checkbox.closest('tr');
                const feeName = row.querySelector('td:nth-child(2) .font-medium').textContent.trim();
                
                // DYNAMIC: Read amounts from data attributes and inputs
                const originalAmount = parseFloat(checkbox.dataset.amount || 0);
                const paidAmount = parseFloat(checkbox.dataset.paidAmount || row.dataset.paidAmount || 0);
                const discountPaid = parseFloat(checkbox.dataset.discountPaid || row.dataset.discountPaid || 0);
                
                const discountInput = row.querySelector(`input[name="discount_${checkbox.value}"]`);
                const currentDiscount = discountInput ? parseFloat(discountInput.value || 0) : 0;
                
                const payableInput = row.querySelector(`input[name="payable_${checkbox.value}"]`);
                
                // DYNAMIC: Calculate remaining balance and payable amount
                const remainingBalance = originalAmount - (paidAmount + discountPaid);
                const maxPayable = Math.max(0, remainingBalance);
                const currentPayable = payableInput ? parseFloat(payableInput.value || maxPayable) : maxPayable;
                const payable = Math.min(currentPayable, maxPayable);
                
                // DYNAMIC: Calculate due amount
                const due = Math.max(0, maxPayable - payable);
                
                totalOriginal += originalAmount;
                totalDiscount += currentDiscount;
                totalPayable += payable;
                totalDue += due;
                
                const feeItem = document.createElement('div');
                feeItem.className = 'flex justify-between text-sm py-1 border-b border-gray-200';
                feeItem.innerHTML = `
                    <span class="font-medium">${feeName}</span>
                    <div class="text-right">
                        <div class="text-xs text-gray-500">Amount: ₹${amount.toFixed(2)}</div>
                        ${discount > 0 ? `<div class="text-xs text-green-600">Discount: -₹${discount.toFixed(2)}</div>` : ''}
                        <div class="font-semibold text-purple-600">Payable: ₹${payable.toFixed(2)}</div>
                    </div>
                `;
                feesList.appendChild(feeItem);
            });
            
            // Update modal totals
            const modalTotalAmount = modal.querySelector('#modalTotalAmount');
            const modalTotalDiscount = modal.querySelector('#modalTotalDiscount');
            const modalTotalPayable = modal.querySelector('#modalTotalPayable');
            const modalTotalDue = modal.querySelector('#modalTotalDue');
            const modalDiscountRow = modal.querySelector('#modalDiscountRow');
            
            if (modalTotalAmount) modalTotalAmount.textContent = `₹ ${totalOriginal.toFixed(2)}`;
            if (modalTotalPayable) modalTotalPayable.textContent = `₹ ${totalPayable.toFixed(2)}`;
            if (modalTotalDue) modalTotalDue.textContent = `₹ ${totalDue.toFixed(2)}`;
            
            if (totalDiscount > 0) {
                if (modalTotalDiscount) modalTotalDiscount.textContent = `₹ ${totalDiscount.toFixed(2)}`;
                if (modalDiscountRow) modalDiscountRow.style.display = 'flex';
            } else {
                if (modalDiscountRow) modalDiscountRow.style.display = 'none';
            }
            
            console.log('✅ [FEES JS] Modal updated:', {
                totalOriginal, totalDiscount, totalPayable, totalDue,
                selectedCount: selectedFees.length
            });
        }
        
        // Position modal correctly within student card
        modal.style.position = 'absolute';
        modal.style.top = '50%';
        modal.style.left = '50%';
        modal.style.transform = 'translate(-50%, -50%)';
        modal.style.zIndex = '50';
        
        // Show overlay and modal
        overlay.style.display = 'block';
        modal.classList.remove('hidden');
        
        // Modal event handlers
        const cancelBtn = modal.querySelector('#cancelPayment');
        const confirmBtn = modal.querySelector('#confirmPayment');
        
        if (cancelBtn) {
            cancelBtn.onclick = () => {
                modal.classList.add('hidden');
                overlay.style.display = 'none';
                document.body.appendChild(modal);
            };
        }
        
        if (confirmBtn) {
            confirmBtn.onclick = () => {
                modal.classList.add('hidden');
                
                // Show processing state
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing Payment...';
                    submitBtn.disabled = true;
                }
                
                // Ensure CSRF token is present
                let csrfInput = form.querySelector('input[name=csrfmiddlewaretoken]');
                if (!csrfInput) {
                    csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrfmiddlewaretoken';
                    csrfInput.value = this.csrfToken || document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
                    form.appendChild(csrfInput);
                }
                
                // Submit form
                console.log('✅ [FEES JS] Submitting payment form');
                form.submit();
            };
        }
    }

    clearModalData(modal) {
        // Clear all modal content to prevent cross-student contamination
        const feesList = modal.querySelector('#modalFeesList');
        if (feesList) feesList.innerHTML = '';
        
        const modalTotalAmount = modal.querySelector('#modalTotalAmount');
        const modalTotalDiscount = modal.querySelector('#modalTotalDiscount');
        const modalTotalPayable = modal.querySelector('#modalTotalPayable');
        const modalTotalDue = modal.querySelector('#modalTotalDue');
        const modalPaymentDate = modal.querySelector('#modalPaymentDate');
        
        if (modalTotalAmount) modalTotalAmount.textContent = '₹ 0.00';
        if (modalTotalDiscount) modalTotalDiscount.textContent = '₹ 0.00';
        if (modalTotalPayable) modalTotalPayable.textContent = '₹ 0.00';
        if (modalTotalDue) modalTotalDue.textContent = '₹ 0.00';
        if (modalPaymentDate) modalPaymentDate.textContent = '-';
        
        console.log('✅ [FEES JS] Modal data cleared');
    }

    getFeeDataFromForm(form) {
        const rows = form.querySelectorAll('.fee-row');
        const feeData = [];
        
        rows.forEach(row => {
            const checkbox = row.querySelector('.fee-checkbox');
            const discountInput = row.querySelector('.discount-input');
            const payableInput = row.querySelector('.payable-input');
            
            if (checkbox) {
                const originalAmount = parseFloat(checkbox.dataset.amount || 0);
                const paidAmount = parseFloat(checkbox.dataset.paidAmount || row.dataset.paidAmount || 0);
                const discountPaid = parseFloat(checkbox.dataset.discountPaid || row.dataset.discountPaid || 0);
                const currentDiscount = discountInput ? parseFloat(discountInput.value || 0) : 0;
                
                // DYNAMIC: Calculate remaining balance
                const remainingBalance = originalAmount - (paidAmount + discountPaid);
                const maxPayable = Math.max(0, remainingBalance);
                
                // DYNAMIC: Get current payable amount
                const customPayable = payableInput ? parseFloat(payableInput.value || maxPayable) : null;
                const actualPayable = customPayable !== null ? Math.min(customPayable, maxPayable) : maxPayable;
                
                feeData.push({
                    id: checkbox.value,
                    selected: checkbox.checked,
                    amount: originalAmount,
                    discount: currentDiscount,
                    paid_amount: paidAmount,
                    discount_paid: discountPaid,
                    custom_payable: customPayable,
                    calculated_payable: actualPayable,
                    calculated_due: Math.max(0, maxPayable - actualPayable)
                });
            }
        });
        
        return feeData;
    }
    


    showMessage(message, type = 'info') {
        document.querySelectorAll('.alert-message').forEach(el => el.remove());

        const messageDiv = document.createElement('div');
        messageDiv.className = `alert-message fixed top-4 right-4 z-50 p-4 rounded-xl shadow-lg animate-slide-in`;

        const colors = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            info: 'bg-blue-500 text-white'
        };

        messageDiv.className += ' ' + (colors[type] || colors.info);

        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };

        messageDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${icons[type] || icons.info} mr-3"></i>
                <span class="font-medium">${message}</span>
            </div>
        `;

        document.body.appendChild(messageDiv);

        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }
}

// Global function for backward compatibility
function loadStudentFees(button) {
    const studentId = button.getAttribute('data-student-id');
    const admissionNumber = button.getAttribute('data-admission-number');
    
    console.log('🔍 [TEMPLATE] loadStudentFees called', {
        button: button,
        studentId: studentId,
        admissionNumber: admissionNumber,
        buttonText: button.textContent.trim(),
        managerAvailable: !!window.consolidatedFeeManager,
        containerId: 'fees-container-' + admissionNumber,
        containerExists: !!document.getElementById('fees-container-' + admissionNumber)
    });
    
    if (window.consolidatedFeeManager) {
        const event = { target: button };
        window.consolidatedFeeManager.handleViewFeesClick(event);
    } else {
        console.error('ConsolidatedFeeManager not initialized');
    }
}

} // End of ConsolidatedFeeManager class guard

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    try {
        if (!window.consolidatedFeeManager && typeof ConsolidatedFeeManager !== 'undefined') {
            window.consolidatedFeeManager = new ConsolidatedFeeManager();
            console.log('✅ [FEES JS] ConsolidatedFeeManager initialized successfully');
        }
    } catch (error) {
        console.error('❌ [FEES JS] Failed to initialize ConsolidatedFeeManager:', error);
    }
});

// Fallback initialization for immediate execution
if (document.readyState === 'loading') {
    // DOM is still loading
} else {
    // DOM is already loaded
    try {
        if (!window.consolidatedFeeManager && typeof ConsolidatedFeeManager !== 'undefined') {
            window.consolidatedFeeManager = new ConsolidatedFeeManager();
            console.log('✅ [FEES JS] ConsolidatedFeeManager initialized (fallback)');
        }
    } catch (error) {
        console.error('❌ [FEES JS] Fallback initialization failed:', error);
    }
}