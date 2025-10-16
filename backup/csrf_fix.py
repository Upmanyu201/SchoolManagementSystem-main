# CSRF Token Fix for Backup System
from django.middleware.csrf import get_token
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

@ensure_csrf_cookie
@login_required
@require_http_methods(["GET"])
def get_csrf_token(request):
    """
    Endpoint to get CSRF token for AJAX requests
    """
    token = get_token(request)
    return JsonResponse({
        'csrf_token': token,
        'status': 'success'
    })

@ensure_csrf_cookie
@login_required  
def backup_page_with_csrf(request):
    """
    Backup page view that ensures CSRF cookie is set
    """
    from django.shortcuts import render
    
    # Ensure CSRF token is available
    token = get_token(request)
    
    # Add token to context
    context = {
        'csrf_token': token
    }
    
    return render(request, 'backup/backup_restore.html', context)