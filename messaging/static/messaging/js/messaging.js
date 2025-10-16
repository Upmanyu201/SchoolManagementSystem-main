// Enhanced Messaging Dashboard JavaScript with Professional UX

class MessagingApp {
    constructor() {
        this.currentMessageData = {};
        this.scrollPosition = 0;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupCharacterCounters();
        this.setupTableSearch();
        this.setupAnimations();
    }

    setupEventListeners() {
        // Search and filter functionality
        const searchInput = document.getElementById('searchContacts');
        const roleFilter = document.getElementById('roleFilter');
        const classFilter = document.getElementById('classFilter');
        
        if (searchInput) searchInput.addEventListener('input', () => this.filterContacts());
        if (roleFilter) roleFilter.addEventListener('change', () => this.filterContacts());
        if (classFilter) classFilter.addEventListener('change', () => this.filterContacts());

        // Modal event listeners
        document.addEventListener('DOMContentLoaded', () => {
            // Bootstrap 5 modal events
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                modal.addEventListener('hidden.bs.modal', () => this.resetModal(modal));
            });
        });
    }

    setupCharacterCounters() {
        const textareas = [
            { id: 'messageContent', counterId: 'charCount' },
            { id: 'bulkMessageContent', counterId: 'bulkCharCount' },
            { id: 'classMessageContent', counterId: 'classCharCount' }
        ];

        textareas.forEach(({ id, counterId }) => {
            const textarea = document.getElementById(id);
            const counter = document.getElementById(counterId);
            
            if (textarea && counter) {
                textarea.addEventListener('input', () => {
                    const count = textarea.value.length;
                    counter.textContent = count;
                    counter.style.color = count > 900 ? '#dc3545' : count > 700 ? '#ffc107' : '#28a745';
                });
            }
        });
    }

    setupTableSearch() {
        const searchInput = document.getElementById('searchContacts');
        if (searchInput) {
            // Add search icon animation
            searchInput.addEventListener('focus', () => {
                searchInput.style.transform = 'scale(1.02)';
            });
            
            searchInput.addEventListener('blur', () => {
                searchInput.style.transform = 'scale(1)';
            });
        }
    }

    setupAnimations() {
        // Intersection Observer for fade-in animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        document.querySelectorAll('.fade-in').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'all 0.6s ease';
            observer.observe(el);
        });
    }

    filterContacts() {
        const searchTerm = document.getElementById('searchContacts')?.value.toLowerCase() || '';
        const selectedRole = document.getElementById('roleFilter')?.value || '';
        const selectedClass = document.getElementById('classFilter')?.value || '';
        const rows = document.querySelectorAll('#contactsTable tbody tr');
        
        let visibleCount = 0;
        
        rows.forEach(row => {
            const name = row.cells[0].textContent.toLowerCase();
            const phone = row.cells[1].textContent.toLowerCase();
            const role = row.dataset.role;
            const classInfo = row.dataset.class;
            
            const matchesSearch = name.includes(searchTerm) || phone.includes(searchTerm);
            const matchesRole = !selectedRole || role === selectedRole;
            const matchesClass = !selectedClass || classInfo.includes(selectedClass);
            
            const isVisible = matchesSearch && matchesRole && matchesClass;
            row.style.display = isVisible ? '' : 'none';
            
            if (isVisible) {
                visibleCount++;
                // Add stagger animation
                setTimeout(() => {
                    row.style.opacity = '1';
                    row.style.transform = 'translateX(0)';
                }, visibleCount * 50);
            } else {
                row.style.opacity = '0';
                row.style.transform = 'translateX(-20px)';
            }
        });

        // Update results count
        this.updateResultsCount(visibleCount);
    }

    updateResultsCount(count) {
        let countElement = document.getElementById('resultsCount');
        if (!countElement) {
            countElement = document.createElement('div');
            countElement.id = 'resultsCount';
            countElement.className = 'text-muted small mb-3';
            document.querySelector('.contacts-section h5').after(countElement);
        }
        countElement.textContent = `Showing ${count} contacts`;
    }

    showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification-toast ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            min-width: 350px;
            max-width: 500px;
            padding: 16px 20px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transform: translateX(400px);
            transition: all 0.3s ease;
            font-weight: 500;
        `;
        
        const colors = {
            success: 'background: linear-gradient(135deg, #10b981, #059669); color: white;',
            error: 'background: linear-gradient(135deg, #ef4444, #dc2626); color: white;',
            warning: 'background: linear-gradient(135deg, #f59e0b, #d97706); color: white;',
            info: 'background: linear-gradient(135deg, #3b82f6, #2563eb); color: white;'
        };
        
        notification.style.cssText += colors[type] || colors.info;
        
        const icons = {
            success: '✅',
            error: '❌', 
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 20px;">${icons[type] || icons.info}</span>
                <div style="flex: 1;">${message}</div>
                <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer; opacity: 0.8; hover: opacity: 1;">×</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.transform = 'translateX(400px)';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }

    saveScrollPosition() {
        this.scrollPosition = window.pageYOffset || document.documentElement.scrollTop;
    }

    restoreScrollPosition() {
        setTimeout(() => {
            window.scrollTo({
                top: this.scrollPosition,
                behavior: 'smooth'
            });
        }, 100);
    }

    showLoadingState(button) {
        if (button) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.textContent = 'Sending...';
        }
    }

    hideLoadingState(button) {
        if (button) {
            button.disabled = false;
            if (button.dataset.originalText) {
                button.textContent = button.dataset.originalText;
            }
        }
    }

    resetModal(modal) {
        const forms = modal.querySelectorAll('form');
        forms.forEach(form => form.reset());
        
        const textareas = modal.querySelectorAll('textarea');
        textareas.forEach(textarea => {
            textarea.value = '';
            const counterId = textarea.id.replace('Content', 'Count').replace('message', 'char').replace('bulk', 'bulkChar').replace('class', 'classChar');
            const counter = document.getElementById(counterId);
            if (counter) counter.textContent = '0';
        });
    }

    // Individual message functions
    sendIndividualMessage(contactType, contactId, messageType, contactName) {
        this.saveScrollPosition();
        
        this.currentMessageData = {
            contact_type: contactType,
            contact_id: contactId,
            message_type: messageType
        };
        
        // Update modal content
        document.getElementById('recipientInfo').textContent = contactName;
        document.getElementById('messageTypeInfo').textContent = messageType === 'WHATSAPP' ? '📱 WhatsApp' : '💬 SMS';
        
        // Update avatar
        const avatar = document.querySelector('#individualMessageModal .avatar-circle');
        if (avatar) {
            avatar.textContent = contactName.charAt(0).toUpperCase();
        }
        
        // Clear previous message
        document.getElementById('messageContent').value = '';
        document.getElementById('charCount').textContent = '0';
        
        // Show modal with scroll restoration on close
        const modal = new bootstrap.Modal(document.getElementById('individualMessageModal'));
        const modalElement = document.getElementById('individualMessageModal');
        
        modalElement.addEventListener('hidden.bs.modal', () => {
            this.restoreScrollPosition();
        }, { once: true });
        
        modal.show();
    }

    async sendMessage() {
        console.log('sendMessage called');
        const messageContent = document.getElementById('messageContent').value.trim();
        const sendButton = document.querySelector('#individualMessageModal .btn-primary');
        
        console.log('Message content:', messageContent);
        console.log('Current message data:', this.currentMessageData);
        
        if (!messageContent) {
            alert('Please enter a message');
            return;
        }
        
        this.showLoadingState(sendButton);
        
        const data = {
            ...this.currentMessageData,
            message: messageContent
        };
        
        console.log('Sending data:', data);
        
        try {
            const response = await fetch('/messaging/send-individual/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            
            console.log('Response status:', response.status);
            const result = await response.json();
            console.log('Response result:', result);
            
            if (result.success) {
                if (result.whatsapp_url) {
                    window.open(result.whatsapp_url, '_blank');
                    alert('WhatsApp opened successfully!');
                } else {
                    alert('Message sent successfully!');
                }
                bootstrap.Modal.getInstance(document.getElementById('individualMessageModal')).hide();
            } else {
                alert('Error: ' + (result.message || result.error));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while sending the message: ' + error.message);
        } finally {
            this.hideLoadingState(sendButton);
        }
    }

    // Bulk message functions
    showBulkMessageModal(recipientType) {
        this.saveScrollPosition();
        
        let recipientText = '';
        switch(recipientType) {
            case 'ALL_STUDENTS':
                recipientText = '📚 All Students';
                break;
            case 'ALL_TEACHERS':
                recipientText = '👨🏫 All Teachers';
                break;
        }
        
        document.getElementById('bulkRecipientInfo').textContent = recipientText;
        document.getElementById('bulkMessageContent').value = '';
        document.getElementById('bulkCharCount').textContent = '0';
        
        this.currentMessageData.recipient_type = recipientType;
        
        const modal = new bootstrap.Modal(document.getElementById('bulkMessageModal'));
        const modalElement = document.getElementById('bulkMessageModal');
        
        modalElement.addEventListener('hidden.bs.modal', () => {
            this.restoreScrollPosition();
        }, { once: true });
        
        modal.show();
    }

    async sendBulkMessage() {
        console.log('sendBulkMessage called');
        const messageContent = document.getElementById('bulkMessageContent').value.trim();
        const messageType = document.querySelector('input[name="bulkMessageType"]:checked').value;
        const sendButton = document.querySelector('#bulkMessageModal .btn-primary');
        
        if (!messageContent) {
            alert('Please enter a message');
            return;
        }
        
        this.showLoadingState(sendButton);
        
        const data = {
            recipient_type: this.currentMessageData.recipient_type,
            message_type: messageType,
            message: messageContent
        };
        
        console.log('Bulk message data:', data);
        
        try {
            const response = await fetch('/messaging/send-bulk/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            console.log('Bulk result:', result);
            
            if (result.success) {
                if (result.whatsapp_urls) {
                    alert(`Opening ${result.whatsapp_urls.length} WhatsApp tabs...`);
                    result.whatsapp_urls.forEach((contact, index) => {
                        setTimeout(() => {
                            window.open(contact.url, '_blank');
                        }, index * 1000);
                    });
                } else {
                    alert(`Bulk messages sent! Success: ${result.successful || 0}`);
                }
                bootstrap.Modal.getInstance(document.getElementById('bulkMessageModal')).hide();
            } else {
                alert('Bulk messaging failed: ' + result.message);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while sending messages: ' + error.message);
        } finally {
            this.hideLoadingState(sendButton);
        }
    }

    // Class message functions
    showClassMessageModal() {
        this.saveScrollPosition();
        
        document.getElementById('classSelect').value = '';
        document.getElementById('classMessageContent').value = '';
        document.getElementById('classCharCount').textContent = '0';
        
        const modal = new bootstrap.Modal(document.getElementById('classMessageModal'));
        const modalElement = document.getElementById('classMessageModal');
        
        modalElement.addEventListener('hidden.bs.modal', () => {
            this.restoreScrollPosition();
        }, { once: true });
        
        modal.show();
    }

    async sendClassMessage() {
        console.log('sendClassMessage called');
        const classId = document.getElementById('classSelect').value;
        const messageContent = document.getElementById('classMessageContent').value.trim();
        const messageType = document.querySelector('input[name="classMessageType"]:checked').value;
        const sendButton = document.querySelector('#classMessageModal .btn-primary');
        
        if (!classId) {
            alert('Please select a class');
            return;
        }
        
        if (!messageContent) {
            alert('Please enter a message');
            return;
        }
        
        this.showLoadingState(sendButton);
        
        const data = {
            recipient_type: 'CLASS_STUDENTS',
            message_type: messageType,
            message: messageContent,
            class_id: classId
        };
        
        console.log('Class message data:', data);
        
        try {
            const response = await fetch('/messaging/send-bulk/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            console.log('Class result:', result);
            
            if (result.success) {
                const className = document.getElementById('classSelect').selectedOptions[0]?.text || 'Selected Class';
                
                if (result.whatsapp_urls) {
                    alert(`Opening WhatsApp for ${className} - ${result.whatsapp_urls.length} students`);
                    result.whatsapp_urls.forEach((contact, index) => {
                        setTimeout(() => {
                            window.open(contact.url, '_blank');
                        }, index * 1000);
                    });
                } else {
                    alert(`Class messages sent to ${className}! Success: ${result.successful || 0}`);
                }
                bootstrap.Modal.getInstance(document.getElementById('classMessageModal')).hide();
            } else {
                alert('Class messaging failed: ' + result.message);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while sending messages: ' + error.message);
        } finally {
            this.hideLoadingState(sendButton);
        }
    }

    updateContactStatus(contactId, status) {
        // Find the contact row and add visual feedback
        const rows = document.querySelectorAll('#contactsTable tbody tr');
        rows.forEach(row => {
            const buttons = row.querySelectorAll('button');
            buttons.forEach(button => {
                if (button.onclick && button.onclick.toString().includes(contactId)) {
                    if (status === 'sent') {
                        // Add a small indicator that message was sent
                        const indicator = document.createElement('span');
                        indicator.className = 'message-sent-indicator';
                        indicator.innerHTML = ' ✓';
                        indicator.style.cssText = 'color: #10b981; font-weight: bold; font-size: 12px;';
                        
                        if (!button.querySelector('.message-sent-indicator')) {
                            button.appendChild(indicator);
                            
                            // Remove indicator after 10 seconds
                            setTimeout(() => {
                                if (indicator.parentNode) {
                                    indicator.remove();
                                }
                            }, 10000);
                        }
                    }
                }
            });
        });
    }

    getCookie(name) {
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
}

// Initialize the messaging app
const messagingApp = new MessagingApp();

// Global functions for backward compatibility
function sendIndividualMessage(contactType, contactId, messageType, contactName) {
    messagingApp.sendIndividualMessage(contactType, contactId, messageType, contactName);
}

function sendMessage() {
    messagingApp.sendMessage();
}

function showBulkMessageModal(recipientType) {
    messagingApp.showBulkMessageModal(recipientType);
}

function sendBulkMessage() {
    messagingApp.sendBulkMessage();
}

function showClassMessageModal() {
    messagingApp.showClassMessageModal();
}

function sendClassMessage() {
    messagingApp.sendClassMessage();
}