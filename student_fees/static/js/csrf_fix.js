// CSRF Token Fix for Fee Processing
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Configure CSRF for all AJAX requests
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

// Fee processing with CSRF protection
function submitFeePayment(formData) {
    return $.ajax({
        url: '/student-fees/submit-deposit/',
        type: 'POST',
        data: formData,
        headers: {
            'X-CSRFToken': csrftoken
        },
        success: function(response) {
            if (response.status === 'success') {
                showSuccessMessage(response.message);
                if (response.redirect_url) {
                    window.location.href = response.redirect_url;
                }
            } else {
                showErrorMessage(response.message);
            }
        },
        error: function(xhr, status, error) {
            showErrorMessage('Payment processing failed. Please try again.');
        }
    });
}

function showSuccessMessage(message) {
    // Create success notification
    const alert = $(`
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            <i class="fas fa-check-circle me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
    $('#messages-container').append(alert);
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        alert.fadeOut();
    }, 5000);
}

function showErrorMessage(message) {
    // Create error notification
    const alert = $(`
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-circle me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
    $('#messages-container').append(alert);
}

// Initialize on document ready
$(document).ready(function() {
    // Ensure CSRF token is available for all forms
    $('form').each(function() {
        if (!$(this).find('input[name="csrfmiddlewaretoken"]').length) {
            $(this).append(`<input type="hidden" name="csrfmiddlewaretoken" value="${csrftoken}">`);
        }
    });
});