from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)


def backup_error_handler(get_response):
    """Middleware to handle backup API errors and return JSON responses"""
    
    def middleware(request):
        # Only handle backup API requests
        if not request.path.startswith('/backup/'):
            return get_response(request)
        
        try:
            response = get_response(request)
            return response
        except Exception as e:
            logger.error(f"Backup API error: {e}")
            
            # Return JSON error for API requests
            return JsonResponse({
                'status': 'error',
                'message': 'Internal server error occurred',
                'error_type': 'system_error'
            }, status=500)
    
    return middleware


@csrf_exempt
def handle_backup_404(request, exception=None):
    """Handle 404 errors for backup endpoints"""
    return JsonResponse({
        'status': 'error',
        'message': 'Endpoint not found',
        'error_type': 'not_found'
    }, status=404)


@csrf_exempt  
def handle_backup_500(request):
    """Handle 500 errors for backup endpoints"""
    return JsonResponse({
        'status': 'error',
        'message': 'Internal server error',
        'error_type': 'system_error'
    }, status=500)