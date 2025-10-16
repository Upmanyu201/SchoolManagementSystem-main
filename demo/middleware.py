from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
from .services import LicenseService

class DemoMiddleware:
    """Middleware to check demo status and completely disable demo when licensed"""
    
    EXEMPT_PATHS = [
        '/demo/',
        '/static/',
        '/media/',
        '/admin/',
        '/users/login/',
        '/users/logout/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get demo status first
        demo_status = LicenseService.get_demo_status()
        
        # Add demo status to request for templates
        request.demo_status = demo_status
        
        # If system is fully licensed, disable all demo functionality
        if demo_status.is_licensed:
            # Redirect demo pages to dashboard for licensed users
            if request.path.startswith('/demo/'):
                return redirect('dashboard')
            
            # Continue with normal request processing
            response = self.get_response(request)
            return response
        
        # Skip demo check for exempt paths (demo mode)
        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return self.get_response(request)
        
        # If demo expired, redirect to expired page
        if not demo_status.is_active:
            if request.path != reverse('demo:expired'):
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({
                        'success': False,
                        'message': 'Demo period has expired. Please activate your license.',
                        'redirect': reverse('demo:expired')
                    }, status=403)
                return redirect('demo:expired')
        
        response = self.get_response(request)
        return response