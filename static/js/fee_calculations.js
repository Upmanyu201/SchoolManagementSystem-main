// D:\School-Management-System\School-Management-System-main\student_fees\static\js\fee_calculations.js

// console.log("fee_calculations.js loaded");

export function updateFeeCalculations(form) {
    // Use AtomicFeeCalculator if available
    if (window.atomicFeeCalculator) {
        const feeData = getFeeDataFromForm(form);
        const totals = window.atomicFeeCalculator.calculateFeeTotals(feeData);
        
        updateSummaryDisplay(form, {
            amount: totals.totalAmount,
            discount: totals.totalDiscount,
            payable: totals.totalPayable,
            selected: totals.selectedCount
        });
        
        toggleSubmitButton(form, totals.selectedCount > 0);
        return totals;
    }
    
    // Fallback to original calculation
    const rows = form.querySelectorAll('.fee-row');
    let totalAmount = 0;
    let totalDiscount = 0;
    let totalPayable = 0;
    let selectedCount = 0;

    rows.forEach(row => {
        const checkbox = row.querySelector('.fee-checkbox');
        const amountCell = row.querySelector('.fee-amount');
        const discountInput = row.querySelector('.discount-input');
        const payableCell = row.querySelector('.payable-amount');
        
        if (!checkbox || !amountCell || !payableCell) return;

        const isSelected = checkbox.checked;
        const amount = parseFloat(amountCell.textContent.replace(/[^0-9.]/g, '')) || 0;
        const discount = discountInput ? parseFloat(discountInput.value) || 0 : 0;
        const payable = Math.max(0, amount - discount);

        payableCell.textContent = `₹ ${payable.toFixed(2)}`;
        payableCell.classList.toggle('text-green-600', isSelected);
        payableCell.classList.toggle('text-gray-400', !isSelected);

        if (isSelected) {
            totalAmount += amount;
            totalDiscount += discount;
            totalPayable += payable;
            selectedCount++;
        }
    });

    updateSummaryDisplay(form, {
        amount: totalAmount,
        discount: totalDiscount,
        payable: totalPayable,
        selected: selectedCount
    });

    toggleSubmitButton(form, selectedCount > 0);

    return {
        amount: totalAmount,
        discount: totalDiscount,
        payable: totalPayable,
        selected: selectedCount
    };
}

// This function update all rows
export function updateAllRowDisplays(form) {
    const rows = form.querySelectorAll('.fee-row');
    rows.forEach(row => {
        const { payable, isSelected } = getRowValues(row);
        updateRowDisplay(row, payable, isSelected);
    });
}

export function calculateFeeTotals(form) {
    // Use AtomicFeeCalculator if available
    if (window.atomicFeeCalculator) {
        const feeData = getFeeDataFromForm(form);
        return window.atomicFeeCalculator.calculateFeeTotals(feeData);
    }
    
    // Fallback calculation
    const checkboxes = form.querySelectorAll('.fee-checkbox:checked');
    let amount = 0;
    let discount = 0;

    checkboxes.forEach(cb => {
        const row = cb.closest('.fee-row');
        const { amount: rowAmount, discount: rowDiscount } = getRowValues(row);
        amount += rowAmount;
        discount += rowDiscount;
    });

    const payable = amount - discount;
    return { amount, discount, payable, selected: checkboxes.length };
}

function getRowValues(row) {
    const checkbox = row.querySelector('.fee-checkbox');
    const amountCell = row.querySelector('.fee-amount');
    const discountInput = row.querySelector('.discount-input');
    
    const amount = parseFloat(amountCell?.textContent.replace(/[^0-9.]/g, '') || 0);
    const discount = parseFloat(discountInput?.value || 0);
    const payable = Math.max(0, amount - discount);
    const isSelected = checkbox?.checked || false;
    
    // console.log("getRowValues for row:", { amount, discount, payable, isSelected });
    return { amount, discount, payable, isSelected };
}

function updateRowDisplay(row, payable, isSelected) {
    const payableCell = row.querySelector('.payable-amount');
    if (!payableCell) return;

    payableCell.textContent = `₹ ${payable.toFixed(2)}`;
    payableCell.classList.toggle('text-green-600', isSelected);
    payableCell.classList.toggle('text-gray-400', !isSelected);
    // console.log("updateRowDisplay for row:", row, payable, isSelected);
}

function updateSummaryDisplay(form, { amount, discount, payable }) {
    // console.log("updateSummaryDisplay called with:", { amount, discount, payable });
    const updateElement = (selector, value) => {
        const el = form.querySelector(selector);
        if (el) {
            el.textContent = `₹ ${value.toFixed(2)}`;
            // console.log("Updated element", selector, "to", el.textContent);
        }
    };

    updateElement('#total_selected', amount);
    updateElement('#total_discount', discount);
    updateElement('#total_payable', payable);
}

function toggleSubmitButton(form, enabled) {
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = !enabled;
    }
}

function getFeeDataFromForm(form) {
    const rows = form.querySelectorAll('.fee-row');
    const feeData = [];
    
    rows.forEach(row => {
        const checkbox = row.querySelector('.fee-checkbox');
        const amountCell = row.querySelector('.fee-amount');
        const discountInput = row.querySelector('.discount-input');
        
        if (checkbox && amountCell) {
            const amount = parseFloat(amountCell.textContent.replace(/[^0-9.]/g, '')) || 0;
            const discount = discountInput ? parseFloat(discountInput.value) || 0 : 0;
            
            feeData.push({
                selected: checkbox.checked,
                amount: amount,
                discount: discount
            });
        }
    });
    
    return feeData;
}