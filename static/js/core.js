// D:\School-Management-System\School-Management-System-main\student_fees\static\js\core.js
// Shared utilities
export function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

export function showFormError(form, message) {
    const errorContainer = form.querySelector('#form-error-container') || document.body;
    errorContainer.innerHTML = `
        <div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-4">
            ${message}
        </div>
    `;
    errorContainer.classList.remove('hidden');
}

export function debounce(func, timeout = 300) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => { func.apply(this, args); }, timeout);
    };
}
