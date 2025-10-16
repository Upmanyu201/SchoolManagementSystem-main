
// Safe JavaScript utilities for School Management System
window.SMS = window.SMS || {};

SMS.safeGetElement = function(id) {
    const element = document.getElementById(id);
    if (!element) {
        console.warn(`Element with id '${id}' not found`);
        return {
            addEventListener: function() {},
            removeEventListener: function() {},
            classList: { add: function() {}, remove: function() {}, toggle: function() {} },
            style: {},
            textContent: '',
            innerHTML: '',
            value: '',
            disabled: false,
            files: []
        };
    }
    return element;
};

SMS.safeQuerySelector = function(selector) {
    const element = document.querySelector(selector);
    if (!element) {
        console.warn(`Element with selector '${selector}' not found`);
        return SMS.safeGetElement('nonexistent');
    }
    return element;
};

// Override getElementById globally for safety
const originalGetElementById = document.getElementById;
document.getElementById = function(id) {
    return SMS.safeGetElement(id);
};

// Safe event listener addition
SMS.addSafeEventListener = function(elementId, event, handler) {
    const element = SMS.safeGetElement(elementId);
    if (element && element.addEventListener) {
        element.addEventListener(event, handler);
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('SMS Safe JavaScript initialized');
});
