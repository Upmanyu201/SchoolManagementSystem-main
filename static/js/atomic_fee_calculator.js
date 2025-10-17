/**
 * ATOMIC FEE CALCULATOR - Frontend Single Source of Truth
 * Matches backend AtomicFeeCalculator for consistent calculations
 */

class AtomicFeeCalculator {
    constructor() {
        this.DECIMAL_PLACES = 2;
        this.cache = new Map();
        this.CACHE_TIMEOUT = 300000; // 5 minutes
    }

    /**
     * Normalize decimal values consistently
     */
    toDecimal(value) {
        if (value === null || value === undefined || value === '') {
            return 0.00;
        }
        return Math.round(parseFloat(value) * 100) / 100;
    }

    /**
     * Generate cache key
     */
    getCacheKey(prefix, studentId, ...args) {
        return [prefix, studentId, ...args].join('_');
    }

    /**
     * Get cached value with expiration
     */
    getCache(key) {
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < this.CACHE_TIMEOUT) {
            return cached.data;
        }
        this.cache.delete(key);
        return null;
    }

    /**
     * Set cache with timestamp
     */
    setCache(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    /**
     * Calculate fee totals from form data with Due amounts
     */
    calculateFeeTotals(feeData) {
        let totals = {
            totalAmount: 0.00,
            totalDiscount: 0.00,
            totalPayable: 0.00,
            totalDue: 0.00,
            selectedCount: 0
        };

        if (!feeData || !Array.isArray(feeData)) {
            return totals;
        }

        // CRITICAL FIX: Only process SELECTED fees
        feeData.forEach(fee => {
            if (fee.selected === true) {
                const originalAmount = this.toDecimal(fee.amount);
                const paidAmount = this.toDecimal(fee.paid_amount || 0);
                const discountPaid = this.toDecimal(fee.discount_paid || 0);
                const currentDiscount = this.toDecimal(fee.discount || 0);
                
                // FIXED: Payable = Original amount - (Paid + DiscountPaid) - Current Discount
                let payableAmount = originalAmount - (paidAmount + discountPaid) - currentDiscount;
                
                // Verify: Payable >= 0
                payableAmount = Math.max(0, payableAmount);
                
                // Store original payable for due calculation
                const originalPayableAmount = payableAmount;
                
                // Handle custom payable if provided
                if (fee.custom_payable !== null && fee.custom_payable !== undefined) {
                    const customPayable = this.toDecimal(fee.custom_payable);
                    // Verify custom payable doesn't exceed max allowed
                    if (customPayable <= originalPayableAmount) {
                        payableAmount = customPayable;
                    }
                }
                
                // FIXED: Due = What remains after this payment
                let dueAmount = Math.max(0, originalPayableAmount - payableAmount);
                
                // If no custom payable set, due should be 0 (paying full amount)
                if (fee.custom_payable === null || fee.custom_payable === undefined) {
                    dueAmount = 0; // Paying full payable amount, so nothing due
                }
                
                // Ensure non-negative values
                payableAmount = Math.max(0, payableAmount);
                dueAmount = Math.max(0, dueAmount);

                totals.totalAmount += originalAmount;
                totals.totalDiscount += currentDiscount;
                totals.totalPayable += payableAmount;
                totals.totalDue += dueAmount;
                totals.selectedCount++;
            }
        });

        // Round final totals
        totals.totalAmount = this.toDecimal(totals.totalAmount);
        totals.totalDiscount = this.toDecimal(totals.totalDiscount);
        totals.totalPayable = this.toDecimal(totals.totalPayable);
        totals.totalDue = this.toDecimal(totals.totalDue);

        return totals;
    }

    /**
     * Update fee display with calculations including Due amounts
     */
    updateFeeDisplay(containerId, feeData) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const totals = this.calculateFeeTotals(feeData);
        
        // CRITICAL FIX: Update Payment Summary totals with proper element selection
        console.log('🔍 [TOTALS] Updating Payment Summary totals:', totals);
        
        // Find elements within the specific container or globally
        const containerElement = document.getElementById(containerId);
        const searchContext = containerElement || document;
        
        // Update Total Selected (Original Amount)
        const totalSelectedElements = [
            searchContext.querySelector('#total_selected'),
            searchContext.querySelector('#total-original'),
            document.getElementById('total_selected'),
            document.getElementById('total-original')
        ].filter(el => el);
        
        totalSelectedElements.forEach(el => {
            el.textContent = `₹ ${totals.totalAmount.toFixed(2)}`;
            console.log(`✅ [TOTALS] Updated ${el.id}: ₹ ${totals.totalAmount.toFixed(2)}`);
        });
        
        // Update Total Discount
        const totalDiscountElements = [
            searchContext.querySelector('#total_discount'),
            searchContext.querySelector('#total-discount'),
            document.getElementById('total_discount'),
            document.getElementById('total-discount')
        ].filter(el => el);
        
        totalDiscountElements.forEach(el => {
            el.textContent = `₹ ${totals.totalDiscount.toFixed(2)}`;
            console.log(`✅ [TOTALS] Updated ${el.id}: ₹ ${totals.totalDiscount.toFixed(2)}`);
        });
        
        // Update Total Payable
        const totalPayableElements = [
            searchContext.querySelector('#total_payable'),
            searchContext.querySelector('#total-payable'),
            searchContext.querySelector('#final-amount'),
            document.getElementById('total_payable'),
            document.getElementById('total-payable'),
            document.getElementById('final-amount')
        ].filter(el => el);
        
        totalPayableElements.forEach(el => {
            el.textContent = `₹ ${totals.totalPayable.toFixed(2)}`;
            console.log(`✅ [TOTALS] Updated ${el.id}: ₹ ${totals.totalPayable.toFixed(2)}`);
        });
        
        // Update Total Due
        const totalDueElements = [
            searchContext.querySelector('#total_due'),
            searchContext.querySelector('#total-due'),
            document.getElementById('total_due'),
            document.getElementById('total-due')
        ].filter(el => el);
        
        totalDueElements.forEach(el => {
            el.textContent = `₹ ${totals.totalDue.toFixed(2)}`;
            console.log(`✅ [TOTALS] Updated ${el.id}: ₹ ${totals.totalDue.toFixed(2)}`);
        });
        
        console.log(`✅ [TOTALS] Payment Summary updated - Selected: ${totalSelectedElements.length}, Discount: ${totalDiscountElements.length}, Payable: ${totalPayableElements.length}, Due: ${totalDueElements.length}`);
        
        // FORCE VISUAL UPDATE: Trigger a repaint to ensure changes are visible
        totalSelectedElements.concat(totalDiscountElements, totalPayableElements, totalDueElements).forEach(el => {
            if (el) {
                el.style.opacity = '0.9';
                setTimeout(() => { el.style.opacity = '1'; }, 50);
            }
        });

        // Update individual fee rows with visual feedback
        container.querySelectorAll('.fee-row').forEach((row, index) => {
            const checkbox = row.querySelector('.fee-checkbox');
            const fee = feeData.find(f => f.id === checkbox?.value);
            
            if (checkbox && fee) {
                // Visual feedback for selected rows
                if (fee.selected) {
                    row.classList.add('bg-green-50', 'border-green-200');
                } else {
                    row.classList.remove('bg-green-50', 'border-green-200');
                }
                
                const originalAmount = this.toDecimal(fee.amount);
                const paidAmount = this.toDecimal(fee.paid_amount || 0);
                const discountPaid = this.toDecimal(fee.discount_paid || 0);
                const currentDiscount = this.toDecimal(fee.discount || 0);
                
                // FIXED: Payable = Original amount - (Paid + DiscountPaid) - Current Discount
                let payableAmount = originalAmount - (paidAmount + discountPaid) - currentDiscount;
                
                // Verify: Payable >= 0
                payableAmount = Math.max(0, payableAmount);
                const maxAllowedPayable = payableAmount;
                
                // CORRECTED: Due = What remains unpaid after this payment
                // If paying full payable amount, due = 0
                // If paying partial amount, due = remaining balance
                let dueAmount = 0; // Default: paying full amount means nothing due
                
                payableAmount = Math.max(0, payableAmount);
                dueAmount = Math.max(0, dueAmount);
                
                // Update fee object with calculated values
                fee.calculated_payable = payableAmount;
                fee.calculated_due = dueAmount;
                
                // Create or update editable payable input for partial payments
                let payableInput = row.querySelector(`input[name="payable_${fee.id}"]`);
                const payableSpan = row.querySelector('.payable-amount');
                
                if (!payableInput && payableSpan) {
                    // Replace span with editable input
                    payableInput = document.createElement('input');
                    payableInput.type = 'number';
                    payableInput.name = `payable_${fee.id}`;
                    payableInput.className = 'w-20 px-2 py-1 border rounded text-right payable-input';
                    payableInput.min = '0';
                    payableInput.max = payableAmount.toFixed(2);
                    payableInput.step = '10.0';
                    payableInput.value = payableAmount.toFixed(2);
                    
                    // Add event listener for payable input changes
                    payableInput.addEventListener('input', () => {
                        const newPayable = parseFloat(payableInput.value || 0);
                        const maxPayable = parseFloat(payableInput.max);
                        
                        if (newPayable > maxPayable) {
                            //payableInput.value = maxPayable.toFixed(2);
                            alert(`Payable amount cannot exceed ₹${maxPayable.toFixed(2)}`);
                        }
                        
                                // FIXED: Due = What remains unpaid after this payment
                        const originalPayableAmount = parseFloat(payableInput.max);
                        let newDue = Math.max(0, originalPayableAmount - newPayable);
                        const dueSpan = row.querySelector('.due-amount');
                        if (dueSpan) dueSpan.textContent = `₹ ${newDue.toFixed(2)}`;
                        
                        // Update hidden due input
                        let dueInput = row.querySelector(`input[name="due_${fee.id}"]`);
                        if (!dueInput) {
                            dueInput = document.createElement('input');
                            dueInput.type = 'hidden';
                            dueInput.name = `due_${fee.id}`;
                            row.appendChild(dueInput);
                        }
                        dueInput.value = newDue.toFixed(2);
                        
                        // Store updated fee data for totals calculation
                        fee.custom_payable = newPayable;
                        fee.due = newDue;
                        
                        // Trigger totals update
                        setTimeout(() => {
                            if (window.consolidatedFeeManager) {
                                const form = row.closest('form');
                                if (form) window.consolidatedFeeManager.updateTotals(form);
                            }
                        }, 100);
                    });
                    
                    payableSpan.parentNode.replaceChild(payableInput, payableSpan);
                } else if (payableInput) {
                    // Update existing input - PRESERVE user's custom value
                    payableInput.max = payableAmount.toFixed(2);
                    
                    // Only update value if input is empty or exceeds max
                    const currentValue = parseFloat(payableInput.value || 0);
                    if (currentValue < 0 || currentValue > payableAmount) {
                        payableInput.value = payableAmount.toFixed(2);
                    }
                    // Otherwise preserve user's custom input
                } else if (payableSpan) {
                    // Update span if no input needed
                    payableSpan.textContent = `₹ ${payableAmount.toFixed(2)}`;
                }
                
                // Update due display: Due = What remains unpaid after this payment
                const currentPayableValue = payableInput ? parseFloat(payableInput.value || 0) : payableAmount;
                const originalPayableAmount = originalAmount - (paidAmount + discountPaid); // True original payable
                
                // FIXED: Due calculation - what remains after payment
                let actualDueAmount = Math.max(0, originalPayableAmount - currentPayableValue);
                
                const dueSpan = row.querySelector('.due-amount');
                if (dueSpan) {
                    dueSpan.textContent = `₹ ${actualDueAmount.toFixed(2)}`;
                    console.log(`🔍 [DUE CALC] Fee ${fee.id}: Payable=${currentPayableValue}, Discount=${currentDiscount}, Due=${actualDueAmount}, OriginalPayable=${originalPayableAmount}, PaidAmount=${paidAmount}`);
                }
                
                // Update hidden due input
                let dueInput = row.querySelector(`input[name="due_${fee.id}"]`);
                if (!dueInput) {
                    dueInput = document.createElement('input');
                    dueInput.type = 'hidden';
                    dueInput.name = `due_${fee.id}`;
                    row.appendChild(dueInput);
                }
                dueInput.value = actualDueAmount.toFixed(2);
            }
        });
    }

    /**
     * Helper to update element text content - ENHANCED
     */
    updateElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
            console.log(`✅ [UPDATE] ${elementId}: ${value}`);
            return true;
        } else {
            console.log(`⚠️ [UPDATE] Element not found: ${elementId}`);
            return false;
        }
    }

    /**
     * Format currency display
     */
    formatCurrency(amount) {
        return `₹ ${this.toDecimal(amount).toFixed(2)}`;
    }

    /**
     * Validate payment data before submission
     */
    validatePayment(paymentData) {
        const errors = [];

        if (!paymentData.selected_fees || paymentData.selected_fees.length === 0) {
            errors.push('Please select at least one fee to pay');
        }

        if (!paymentData.payment_mode) {
            errors.push('Please select a payment mode');
        }

        let totalPayable = 0;
        paymentData.selected_fees.forEach(fee => {
            const amount = this.toDecimal(fee.amount);
            const discount = this.toDecimal(fee.discount || 0);
            const payable = amount - discount;

            if (payable < 0) {
                errors.push(`Invalid amount for ${fee.display_name}`);
            }

            totalPayable += payable;
        });

        if (totalPayable < 0) {
            errors.push('Total payable amount must be greater than zero');
        }

        return {
            isValid: errors.length === 0,
            errors: errors,
            totalPayable: this.toDecimal(totalPayable)
        };
    }

    /**
     * Process payment with validation
     */
    async processPayment(studentId, paymentData) {
        const validation = this.validatePayment(paymentData);
        
        if (!validation.isValid) {
            return {
                success: false,
                errors: validation.errors
            };
        }

        try {
            const response = await fetch('/student_fees/process_payment/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    student_id: studentId,
                    payment_data: paymentData
                })
            });

            const result = await response.json();
            
            if (result.success) {
                // Clear cache for student
                this.clearStudentCache(studentId);
            }

            return result;

        } catch (error) {
            console.error('Payment processing error:', error);
            return {
                success: false,
                errors: ['Payment processing failed. Please try again.']
            };
        }
    }

    /**
     * Get CSRF token from cookie
     */
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }

    /**
     * Clear cached data for student
     */
    clearStudentCache(studentId) {
        const keysToDelete = [];
        for (let key of this.cache.keys()) {
            if (key.includes(`_${studentId}_`)) {
                keysToDelete.push(key);
            }
        }
        keysToDelete.forEach(key => this.cache.delete(key));
    }

    /**
     * Load student fees with caching
     */
    async loadStudentFees(studentId, forceRefresh = false) {
        const cacheKey = this.getCacheKey('student_fees', studentId);
        
        if (!forceRefresh) {
            const cached = this.getCache(cacheKey);
            if (cached) {
                return cached;
            }
        }

        try {
            const response = await fetch(`/student_fees/api/student/${studentId}/fees/`);
            const data = await response.json();
            
            if (data.success) {
                this.setCache(cacheKey, data);
                return data;
            } else {
                throw new Error(data.message || 'Failed to load student fees');
            }

        } catch (error) {
            console.error('Error loading student fees:', error);
            return {
                success: false,
                message: 'Failed to load student fees'
            };
        }
    }

    /**
     * Initialize fee calculator for a form
     */
    initializeForm(formId, studentId) {
        const form = document.getElementById(formId);
        if (!form) return;

        // Add event listeners for fee selection
        form.addEventListener('change', (e) => {
            if (e.target.type === 'checkbox' && e.target.name === 'selected_fees') {
                this.handleFeeSelection(formId, studentId);
            }
        });

        // Add event listeners for discount changes
        form.addEventListener('input', (e) => {
            if (e.target.name && e.target.name.includes('discount')) {
                this.handleDiscountChange(formId, studentId);
            }
        });

        // Load initial data
        this.loadStudentFees(studentId).then(data => {
            if (data.success) {
                this.updateFeeDisplay(formId, data.fees);
            }
        });
    }

    /**
     * Handle fee selection changes with Due calculation
     */
    handleFeeSelection(formId, studentId) {
        const form = document.getElementById(formId);
        const checkboxes = form.querySelectorAll('input[name="selected_fees"]:checked');
        
        const selectedFees = Array.from(checkboxes).map(cb => {
            const feeRow = cb.closest('.fee-row');
            const discountInput = feeRow.querySelector('.discount-input');
            const payableInput = feeRow.querySelector('.payable-input');
            
            return {
                id: cb.value,
                amount: parseFloat(cb.dataset.amount || 0),
                paid_amount: parseFloat(feeRow.dataset.paidAmount || 0),
                discount_paid: parseFloat(feeRow.dataset.discountPaid || 0),
                discount: parseFloat(discountInput?.value || 0),
                payable: parseFloat(payableInput?.value || 0),
                due: parseFloat(feeRow.querySelector('.due-amount')?.textContent.replace('₹ ', '') || 0),
                selected: true
            };
        });

        this.updateFeeDisplay(formId, selectedFees);
    }

    /**
     * Handle discount changes
     */
    handleDiscountChange(formId, studentId) {
        this.handleFeeSelection(formId, studentId);
    }
}

// Global instance
window.atomicFeeCalculator = new AtomicFeeCalculator();

// Auto-initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any forms with data-fee-calculator attribute
    const feeCalculatorForms = document.querySelectorAll('[data-fee-calculator]');
    feeCalculatorForms.forEach(form => {
        const studentId = form.dataset.studentId;
        if (studentId) {
            window.atomicFeeCalculator.initializeForm(form.id, studentId);
        }
    });
    
    console.log('✅ [ATOMIC CALC] AtomicFeeCalculator initialized and ready');
});