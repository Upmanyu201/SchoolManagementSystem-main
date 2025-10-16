from django.http import HttpResponse, Http404
from django.conf import settings
from django.views.static import serve
import os

def serve_media_with_fallback(request, path):
    """Serve media files with fallback to default image for missing files"""
    try:
        # Try to serve the actual file
        return serve(request, path, document_root=settings.MEDIA_ROOT)
    except Http404:
        # If file not found and it's an image request, serve default placeholder
        if path.startswith('students/images/') and any(path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
            # Return a simple SVG placeholder
            svg_content = '''<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
                <rect width="100" height="100" fill="#e5e7eb"/>
                <text x="50" y="50" text-anchor="middle" dy=".3em" fill="#6b7280" font-family="Arial" font-size="12">No Image</text>
            </svg>'''
            return HttpResponse(svg_content, content_type='image/svg+xml')
        
        # For non-image files, raise 404
        raise Http404("Media file not found")