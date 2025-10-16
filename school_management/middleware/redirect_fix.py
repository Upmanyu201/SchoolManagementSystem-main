# school_management/middleware/redirect_fix.py
# D:\School-Management-System-main\school_management\middleware\redirect_fix.py

from django.shortcuts import redirect

class RedirectLoopFixMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/' and request.GET.get('next') == '/' and not request.user.is_authenticated:
            return redirect('/dashboard/')
        return self.get_response(request)
