# Standardized Response Handler for Backup System
from django.http import JsonResponse
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger('backup.responses')

class BackupResponseHandler:
    """Standardized response handler for consistent API responses"""
    
    @staticmethod
    def success(message: str, data: Optional[Dict[str, Any]] = None, status_code: int = 200) -> JsonResponse:
        """Create standardized success response"""
        response_data = {
            'status': 'success',
            'message': message
        }
        
        if data:
            response_data['data'] = data
        
        return JsonResponse(response_data, status=status_code)
    
    @staticmethod
    def error(message: str, error_type: str = 'general_error', 
              details: Optional[str] = None, status_code: int = 400) -> JsonResponse:
        """Create standardized error response"""
        response_data = {
            'status': 'error',
            'message': message,
            'error_type': error_type
        }
        
        if details:
            response_data['details'] = details
        
        return JsonResponse(response_data, status=status_code)
    
    @staticmethod
    def validation_error(message: str, field_errors: Optional[Dict[str, str]] = None) -> JsonResponse:
        """Create validation error response"""
        response_data = {
            'status': 'error',
            'message': message,
            'error_type': 'validation_error'
        }
        
        if field_errors:
            response_data['field_errors'] = field_errors
        
        return JsonResponse(response_data, status=400)
    
    @staticmethod
    def permission_error(message: str = "You do not have permission to perform this action") -> JsonResponse:
        """Create permission error response"""
        return JsonResponse({
            'status': 'error',
            'message': message,
            'error_type': 'permission_error'
        }, status=403)
    
    @staticmethod
    def not_found_error(message: str = "Resource not found") -> JsonResponse:
        """Create not found error response"""
        return JsonResponse({
            'status': 'error',
            'message': message,
            'error_type': 'not_found'
        }, status=404)
    
    @staticmethod
    def server_error(message: str = "An internal server error occurred") -> JsonResponse:
        """Create server error response"""
        return JsonResponse({
            'status': 'error',
            'message': message,
            'error_type': 'server_error'
        }, status=500)
    
    @staticmethod
    def restore_progress(job_id: int, progress: Dict[str, Any]) -> JsonResponse:
        """Create restore progress response"""
        return JsonResponse({
            'status': 'success',
            'job_id': job_id,
            'progress': progress
        })
    
    @staticmethod
    def restore_complete(job_id: int, summary: Dict[str, Any]) -> JsonResponse:
        """Create restore completion response"""
        created = summary.get('created', 0)
        updated = summary.get('updated', 0)
        
        message = f'Restore completed successfully! {created} records created, {updated} updated'
        
        return JsonResponse({
            'status': 'success',
            'message': message,
            'job_id': job_id,
            'summary': summary
        })
    
    @staticmethod
    def backup_complete(job_id: int, filename: str, summary: Optional[Dict[str, Any]] = None) -> JsonResponse:
        """Create backup completion response"""
        response_data = {
            'status': 'success',
            'message': 'Backup created successfully!',
            'job_id': job_id,
            'filename': filename
        }
        
        if summary:
            response_data['summary'] = summary
        
        return JsonResponse(response_data)

# Convenience functions
def success_response(message: str, data: Optional[Dict[str, Any]] = None) -> JsonResponse:
    return BackupResponseHandler.success(message, data)

def error_response(message: str, error_type: str = 'general_error', status_code: int = 400) -> JsonResponse:
    return BackupResponseHandler.error(message, error_type, status_code=status_code)