# Dashboard URLs
from django.urls import path
from .views import dashboard_view, dashboard_stats_api, check_dashboard_updates
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

urlpatterns = [
    path('', login_required(dashboard_view), name='dashboard'),
    path('api/stats/', dashboard_stats_api, name='dashboard_stats_api'),
    path('api/check-updates/', check_dashboard_updates, name='check_dashboard_updates'),
    path('api/force-refresh/', login_required(lambda request: JsonResponse({'success': True, 'message': 'Cache cleared'})), name='force_refresh'),
    path('exports/', login_required(TemplateView.as_view(template_name='exports/export_dashboard.html')), name='export_dashboard'),
]
