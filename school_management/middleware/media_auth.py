import re
from django.conf import settings
from django.shortcuts import redirect

class MediaAuthExemptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [re.compile(url) for url in settings.LOGIN_EXEMPT_URLS]

    def __call__(self, request):
        # Skip middleware for:
        # 1. Media/static files
        # 2. Login page itself
        # 3. URLs in LOGIN_EXEMPT_URLS
        if (
            request.path.startswith(settings.MEDIA_URL) or
            request.path.startswith(settings.STATIC_URL) or
            request.path == settings.LOGIN_URL or
            any(url.match(request.path) for url in self.exempt_urls)
        ):
            return self.get_response(request)
            
        # Require authentication for other URLs
        if not request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
            
        return self.get_response(request)