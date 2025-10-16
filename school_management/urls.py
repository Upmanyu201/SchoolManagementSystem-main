"""
URL configuration for school_management project.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView
from django.views.generic import RedirectView
from django.views.static import serve
from django.http import HttpResponse
import re

# Dashboard Views
from dashboard.views import dashboard_view, dashboard_stats_api
from dashboard.ml_views import ml_insights, student_risk_api, fee_optimization_api
from students.transport_api import student_transport_api
from attendance.dashboard_api import attendance_report_api

# Chrome DevTools handler
def chrome_devtools_handler(request):
    """Handle Chrome DevTools requests silently"""
    return HttpResponse('', status=204)

# Demo Module Access Views
try:
    from demo_module_access import demo_students_view, demo_students_edit, demo_fees_view
    DEMO_AVAILABLE = True
except ImportError:
    DEMO_AVAILABLE = False

# Export system has been removed from the application

def redirect_to_previous_or_login(request):
    """
    Redirect to the previous page from session or to login if no previous page exists.
    If user is authenticated, redirect to dashboard instead of login.
    """
    # Get the previous URL from session
    previous_url = request.session.get('previous_url', None)
    
    if request.user.is_authenticated:
        # If logged in, redirect to dashboard or previous URL
        return redirect(previous_url if previous_url else 'dashboard')
    else:
        # If not logged in, redirect to login with next parameter
        return redirect(f"{settings.LOGIN_URL}?next={previous_url}" if previous_url else settings.LOGIN_URL)

def custom_404_view(request, exception=None):
    """Custom 404 handler that redirects instead of showing 404 page"""
    return redirect_to_previous_or_login(request)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Root URL - redirect to dashboard if authenticated, else to login
    path('', LoginView.as_view(template_name='users/login.html'), name='root'),
    
    # App routes
    path('dashboard/', include('dashboard.urls')),
    path('school_profile/', include('school_profile.urls')),
    path('users/', include('users.urls')),
    path('teachers/', include('teachers.urls')),
    path('students/', include('students.urls')),
    path('students/api/', include('students.api.urls')),
    path('subjects/', include('subjects.urls')),
    path('transport/', include('transport.urls')),
    path('student_fees/', include('student_fees.urls')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    path('fees/', include('fees.urls')),
    path('fines/', include('fines.urls', namespace='fines')),
    path('promotion/', include('promotion.urls')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('backup/', include('backup.urls')),
    path('settings/', include('settings.urls')),
    path('messaging/', include('messaging.urls')),
    path('demo/', include('demo.urls')),  # Demo license management
    
    # API routes
    path('api/dashboard-stats/', dashboard_stats_api, name='api_dashboard_stats'),
    
    # Student API routes
    path('api/students/<str:admission_number>/transport/', student_transport_api, name='student_transport_api'),
    
    # Attendance API routes
    path('attendance/api/report/', attendance_report_api, name='attendance_report_api'),
    
    # ML Dashboard routes
    path('dashboard/ml-insights/', ml_insights, name='ml_insights'),
    path('api/student-risk/<int:student_id>/', student_risk_api, name='student_risk_api'),
    path('api/fee-optimization/', fee_optimization_api, name='fee_optimization_api'),
    
    # ML API Endpoints
    path('api/ml/', include('core.ml_urls')),
    
    # Modern Export System (2025)
    path('core/', include('core.urls')),
    

    
    # Auth redirects
    path('login/', RedirectView.as_view(url='/users/login/', permanent=True), name='login'),
    path('logout/', RedirectView.as_view(url='/users/logout/', permanent=True), name='logout'),
    
    # URL redirects for common mistakes
    path('student_fees/get-student-fees/', RedirectView.as_view(url='/student_fees/ajax/get-student-fees/', permanent=True)),
    path('messaging/api/', RedirectView.as_view(url='/messaging/api/status/', permanent=True)),
    path('fees/setup/', RedirectView.as_view(url='/fees/fees_setup/', permanent=True)),
    
    # REST Framework authentication
    path('api-auth/', include('rest_framework.urls')),
    
    # Chrome DevTools - handle silently to prevent warnings
    path('.well-known/appspecific/com.chrome.devtools.json', chrome_devtools_handler),
    
    # Favicon handler to prevent 404 warnings
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
]

# Add demo URLs if available
if DEMO_AVAILABLE:
    urlpatterns += [
        path('demo/students/', demo_students_view, name='demo_students'),
        path('demo/students/edit/', demo_students_edit, name='demo_students_edit'),
        path('demo/fees/', demo_fees_view, name='demo_fees'),
    ]


# Add the custom 404 handler
handler404 = 'django.views.defaults.page_not_found'

# Static and Media Files (for both development and production)
if settings.DEBUG:
    from core.media_views import serve_media_with_fallback
    urlpatterns += [
        re_path(r'^%s(?P<path>.*)$' % re.escape(settings.MEDIA_URL.lstrip('/')), 
                serve_media_with_fallback, name='media'),
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Production URL patterns
    from core.media_views import serve_media_with_fallback
    urlpatterns += [
        re_path(r'^%s(?P<path>.*)$' % re.escape(settings.MEDIA_URL.lstrip('/')), 
                serve_media_with_fallback, name='media'),
        re_path(r'^%s(?P<path>.*)$' % re.escape(settings.STATIC_URL.lstrip('/')), 
        serve, {'document_root': settings.STATIC_ROOT}),
    ]