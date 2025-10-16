# core/error_handlers.py - Enhanced error handling
from django.http import JsonResponse
from django.shortcuts import render
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling"""
    
    @staticmethod
    def handle_validation_error(error, request=None):
        """Handle validation errors with user-friendly messages"""
        if hasattr(error, 'message_dict'):
            # Form validation errors
            messages = []
            for field, errors in error.message_dict.items():
                for err in errors:
                    messages.append(f"{field.title()}: {err}")
            message = "; ".join(messages)
        else:
            message = str(error)
        
        return {
            'error': 'Validation failed',
            'message': f"Please check your input: {message}",
            'type': 'validation_error'
        }
    
    @staticmethod
    def handle_permission_error(error, request=None):
        """Handle permission errors"""
        return {
            'error': 'Permission denied',
            'message': "You don't have permission to perform this action. Please contact your administrator.",
            'type': 'permission_error'
        }
    
    @staticmethod
    def handle_integrity_error(error, request=None):
        """Handle database integrity errors"""
        error_msg = str(error).lower()
        
        if 'unique' in error_msg:
            message = "This record already exists. Please check for duplicates."
        elif 'foreign key' in error_msg:
            message = "Cannot delete this record as it's being used elsewhere."
        else:
            message = "Database error occurred. Please try again."
        
        return {
            'error': 'Database error',
            'message': message,
            'type': 'integrity_error'
        }
    
    @staticmethod
    def handle_generic_error(error, request=None):
        """Handle generic errors"""
        logger.error(f"Unhandled error: {error}")
        
        return {
            'error': 'System error',
            'message': "Something went wrong. Please try again or contact support.",
            'type': 'system_error'
        }

def api_error_response(error, status_code=400):
    """Generate API error response"""
    if isinstance(error, ValidationError):
        error_data = ErrorHandler.handle_validation_error(error)
    elif isinstance(error, PermissionDenied):
        error_data = ErrorHandler.handle_permission_error(error)
        status_code = 403
    elif isinstance(error, IntegrityError):
        error_data = ErrorHandler.handle_integrity_error(error)
    else:
        error_data = ErrorHandler.handle_generic_error(error)
        status_code = 500
    
    return JsonResponse(error_data, status=status_code)

def web_error_response(error, request, template='error.html'):
    """Generate web error response"""
    if isinstance(error, ValidationError):
        error_data = ErrorHandler.handle_validation_error(error, request)
    elif isinstance(error, PermissionDenied):
        error_data = ErrorHandler.handle_permission_error(error, request)
    elif isinstance(error, IntegrityError):
        error_data = ErrorHandler.handle_integrity_error(error, request)
    else:
        error_data = ErrorHandler.handle_generic_error(error, request)
    
    return render(request, template, {'error': error_data})