import logging
from django.http import Http404
from django.conf import settings
import os

logger = logging.getLogger(__name__)

class FileSecurityMiddleware:
    """Middleware to handle missing file errors gracefully"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """Handle file-related exceptions"""
        if isinstance(exception, (FileNotFoundError, OSError)):
            # Log the missing file error
            logger.warning(f"File access error for user {request.user.id if request.user.is_authenticated else 'anonymous'}: {exception}")
            
            # If it's a media file request, return 404
            if request.path.startswith('/media/'):
                raise Http404("File not found")
        
        return None