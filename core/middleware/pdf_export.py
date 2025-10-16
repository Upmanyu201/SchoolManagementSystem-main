"""
🔧 PDF Export Middleware
Prevents broken pipe errors and handles download manager interference
"""

import logging
import time
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)
export_logger = logging.getLogger('export.api')

class PDFExportMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_times = {}
        super().__init__(get_response)
    
    def process_request(self, request):
        # Track request start time for export endpoints
        if 'export' in request.path:
            self.request_times[id(request)] = time.time()
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
            client_ip = request.META.get('REMOTE_ADDR', 'Unknown')
            
            export_logger.info(
                f"Export Request: {request.method} {request.path} - "
                f"IP: {client_ip} - Agent: {user_agent[:50]}..."
            )
    
    def process_response(self, request, response):
        # Only process PDF responses
        if (response.get('Content-Type') == 'application/pdf' and 
            'export' in request.path):
            
            # Calculate request duration
            request_id = id(request)
            duration = 0
            if request_id in self.request_times:
                duration = time.time() - self.request_times[request_id]
                del self.request_times[request_id]
            
            # Add headers to prevent IDM interference
            response['X-Content-Type-Options'] = 'nosniff'
            response['Referrer-Policy'] = 'no-referrer'
            response['X-Export-Timestamp'] = str(int(time.time()))
            # Prevent frame embedding to force download
            response['X-Frame-Options'] = 'DENY'
            
            # Force download for all browsers
            if 'Content-Disposition' in response:
                current_disp = response['Content-Disposition']
                if 'inline' in current_disp:
                    response['Content-Disposition'] = current_disp.replace('inline', 'attachment')
            else:
                response['Content-Disposition'] = 'attachment'
            
            # Additional headers to force download
            response['Content-Transfer-Encoding'] = 'binary'
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            
            # Detailed logging
            content_size = len(response.content) if hasattr(response, 'content') else 0
            export_logger.info(
                f"PDF Response: {request.path} - "
                f"Size: {content_size} bytes - "
                f"Duration: {duration:.3f}s - "
                f"Status: {response.status_code}"
            )
            
            # Log headers for debugging
            export_logger.debug(
                f"Response Headers: Content-Type: {response.get('Content-Type')} - "
                f"Content-Disposition: {response.get('Content-Disposition')} - "
                f"Content-Length: {response.get('Content-Length')}"
            )
            
        return response
    
    def process_exception(self, request, exception):
        # Handle broken pipe errors gracefully
        if ('Broken pipe' in str(exception) or 
            'ConnectionResetError' in str(exception) or
            'ConnectionAbortedError' in str(exception)):
            
            export_logger.warning(
                f"Connection Interrupted: {request.path} - "
                f"Error: {type(exception).__name__} - "
                f"Message: {str(exception)[:100]}"
            )
            
            # Don't raise the exception, just log it
            return HttpResponse('Download interrupted by client', status=200)
        
        return None
