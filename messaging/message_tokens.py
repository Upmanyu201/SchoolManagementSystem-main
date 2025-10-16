# messaging/message_tokens.py
"""
Token-level messaging system for user-friendly communications
Implements conversational, human-like messaging patterns
"""

class MessageTokens:
    """User-friendly message tokens for different scenarios"""
    
    # Success Messages - Conversational and positive
    SUCCESS = {
        'payment_received': "Great! Your payment of ₹{amount} has been received successfully.",
        'student_enrolled': "Perfect! {student_name} has been enrolled in {class_name}.",
        'fee_updated': "All done! Fee structure has been updated successfully.",
        'sms_sent': "Message sent! Your SMS has been delivered to {count} recipients.",
        'data_saved': "Success! All information has been saved.",
        'export_ready': "Your {report_type} report is ready to download!",
        'backup_complete': "Backup completed successfully! Your data is safe.",
    }
    
    # Error Messages - Helpful and solution-oriented
    ERRORS = {
        'student_not_found': "We couldn't find a student with that admission number. Please check and try again.",
        'payment_failed': "Your payment couldn't be processed right now. Please check your details and try again.",
        'invalid_phone': "Please enter a valid 10-digit mobile number.",
        'missing_fields': "Please fill in all required fields (marked with *) and try again.",
        'file_too_large': "Your file is too large. Please choose a file under 5MB.",
        'network_error': "We're having trouble connecting right now. Please check your internet and try again.",
        'permission_denied': "You don't have permission to access this page. Please contact your administrator.",
        'session_expired': "Your session has expired. Please log in again to continue.",
    }
    
    # Warning Messages - Friendly heads-up
    WARNINGS = {
        'pending_fees': "Just a heads up - {student_name} has pending fees of ₹{amount}.",
        'overdue_payment': "Reminder: {student_name}'s fee payment is overdue by {days} days.",
        'data_will_be_lost': "This action will permanently delete the data. Are you sure you want to continue?",
        'duplicate_entry': "This {item_type} already exists. Please check your entry.",
        'low_balance': "Account balance is running low. Consider adding funds soon.",
    }
    
    # Information Messages - Clear and helpful
    INFO = {
        'processing': "We're processing your request. This may take a moment...",
        'no_results': "No {item_type} found matching your search criteria.",
        'maintenance': "This feature is temporarily under maintenance. Please try again later.",
        'new_notifications': "You have {count} new notifications.",
        'auto_save': "Your changes are being saved automatically.",
        'export_preparing': "Your export is being prepared. We'll notify you when it's ready.",
    }
    
    # SMS Templates - Short and personal
    SMS_TEMPLATES = {
        'fee_reminder': "Hi! {student_name}'s fee of ₹{amount} is due on {due_date}. Pay online: {link} - {school_name}",
        'payment_confirmation': "Payment received! ₹{amount} for {student_name}. Receipt: {receipt_no}. Thank you! - {school_name}",
        'attendance_alert': "Hello! {student_name} was absent today ({date}). Please contact school if needed. - {school_name}",
        'exam_reminder': "{student_name}'s {exam_name} exam is on {date} at {time}. Best wishes! - {school_name}",
        'event_notification': "Reminder: {event_name} on {date}. {student_name} is expected to attend. - {school_name}",
    }
    
    # Form Validation Messages - Specific and actionable
    VALIDATION = {
        'required_field': "This field is required.",
        'invalid_email': "Please enter a valid email address.",
        'password_weak': "Password should be at least 8 characters with numbers and letters.",
        'phone_format': "Please enter phone number in format: 9876543210",
        'date_future': "Date cannot be in the future.",
        'amount_positive': "Amount must be greater than zero.",
        'file_format': "Please upload a PDF or image file only.",
    }
    
    # Loading States - Encouraging
    LOADING = {
        'saving': "Saving your changes...",
        'loading': "Loading...",
        'uploading': "Uploading file...",
        'processing_payment': "Processing your payment...",
        'generating_report': "Generating your report...",
        'sending_messages': "Sending messages...",
    }

class MessageFormatter:
    """Format messages with proper context and personalization"""
    
    @staticmethod
    def format_success(key, **kwargs):
        """Format success message with context"""
        template = MessageTokens.SUCCESS.get(key, "Operation completed successfully.")
        return template.format(**kwargs)
    
    @staticmethod
    def format_error(key, **kwargs):
        """Format error message with helpful context"""
        template = MessageTokens.ERRORS.get(key, "Something went wrong. Please try again.")
        return template.format(**kwargs)
    
    @staticmethod
    def format_warning(key, **kwargs):
        """Format warning message"""
        template = MessageTokens.WARNINGS.get(key, "Please note: Action required.")
        return template.format(**kwargs)
    
    @staticmethod
    def format_info(key, **kwargs):
        """Format information message"""
        template = MessageTokens.INFO.get(key, "Information updated.")
        return template.format(**kwargs)
    
    @staticmethod
    def format_sms(key, **kwargs):
        """Format SMS message with character limit consideration"""
        template = MessageTokens.SMS_TEMPLATES.get(key, "Message from {school_name}")
        message = template.format(**kwargs)
        
        # Ensure SMS is under 160 characters
        if len(message) > 160:
            # Truncate gracefully
            message = message[:157] + "..."
        
        return message
    
    @staticmethod
    def format_validation(key, **kwargs):
        """Format validation message"""
        template = MessageTokens.VALIDATION.get(key, "Please check your input.")
        return template.format(**kwargs)

class ContextualMessaging:
    """Provide contextual messaging based on user actions"""
    
    @staticmethod
    def get_payment_message(amount, student_name, receipt_no):
        """Get contextual payment success message"""
        return MessageFormatter.format_success(
            'payment_received',
            amount=amount,
            student_name=student_name,
            receipt_no=receipt_no
        )
    
    @staticmethod
    def get_fee_reminder_sms(student_name, amount, due_date, school_name, payment_link=None):
        """Get personalized fee reminder SMS"""
        return MessageFormatter.format_sms(
            'fee_reminder',
            student_name=student_name,
            amount=amount,
            due_date=due_date,
            school_name=school_name,
            link=payment_link or "school portal"
        )
    
    @staticmethod
    def get_error_with_solution(error_type, **context):
        """Get error message with suggested solution"""
        base_message = MessageFormatter.format_error(error_type, **context)
        
        # Add contextual help based on error type
        solutions = {
            'student_not_found': " You can search by name or check the student list.",
            'payment_failed': " You can try a different payment method or contact support.",
            'invalid_phone': " Example: 9876543210",
            'permission_denied': " Contact your system administrator for access.",
        }
        
        solution = solutions.get(error_type, "")
        return base_message + solution

# Usage examples for integration
class MessageIntegration:
    """Examples of how to integrate user-friendly messaging"""
    
    @staticmethod
    def django_messages_example(request, message_type, key, **kwargs):
        """Example of Django messages integration"""
        from django.contrib import messages
        
        if message_type == 'success':
            message = MessageFormatter.format_success(key, **kwargs)
            messages.success(request, message)
        elif message_type == 'error':
            message = MessageFormatter.format_error(key, **kwargs)
            messages.error(request, message)
        elif message_type == 'warning':
            message = MessageFormatter.format_warning(key, **kwargs)
            messages.warning(request, message)
        elif message_type == 'info':
            message = MessageFormatter.format_info(key, **kwargs)
            messages.info(request, message)
    
    @staticmethod
    def api_response_example(success, message_key, **kwargs):
        """Example of API response formatting"""
        if success:
            message = MessageFormatter.format_success(message_key, **kwargs)
            return {
                'success': True,
                'message': message,
                'data': kwargs
            }
        else:
            message = MessageFormatter.format_error(message_key, **kwargs)
            return {
                'success': False,
                'message': message,
                'error_code': message_key.upper()
            }