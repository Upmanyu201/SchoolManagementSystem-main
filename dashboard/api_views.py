# Dashboard API Views for Real-time Updates
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.cache import cache
import json
import time
import logging

from .real_time_service import CachedUnifiedDashboardService, DashboardUpdateService

logger = logging.getLogger(__name__)

@never_cache
@login_required
@require_http_methods(["GET"])
def dashboard_stats_api(request):
    """API endpoint for dashboard statistics with caching"""
    try:
        service = CachedUnifiedDashboardService()
        dashboard_data = service.get_complete_dashboard_data()
        
        return JsonResponse({
            'success': True,
            'data': dashboard_data,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Dashboard stats API error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch dashboard data',
            'timestamp': timezone.now().isoformat()
        }, status=500)

@never_cache
@login_required
@require_http_methods(["GET"])
def dashboard_updates_check(request):
    """Check for dashboard updates"""
    try:
        service = CachedUnifiedDashboardService()
        update_info = service.get_real_time_updates()
        
        # Get client's last known update time
        client_last_update = request.GET.get('last_update')
        
        has_new_updates = False
        if client_last_update and update_info['last_update']:
            try:
                from datetime import datetime
                client_time = datetime.fromisoformat(client_last_update.replace('Z', '+00:00'))
                server_time = datetime.fromisoformat(update_info['last_update'])
                has_new_updates = server_time > client_time
            except (ValueError, TypeError):
                has_new_updates = True
        
        return JsonResponse({
            'success': True,
            'has_updates': has_new_updates or update_info['has_updates'],
            'last_update': update_info['last_update'],
            'timestamp': update_info['timestamp']
        })
    except Exception as e:
        logger.error(f"Dashboard updates check error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to check for updates'
        }, status=500)

@never_cache
@login_required
def dashboard_stream(request):
    """Server-Sent Events stream for real-time updates"""
    def event_stream():
        """Generate SSE events"""
        yield "data: {\"type\": \"connected\", \"message\": \"Dashboard stream connected\"}\n\n"
        
        last_check = timezone.now()
        service = CachedUnifiedDashboardService()
        
        while True:
            try:
                # Check for updates every 10 seconds
                time.sleep(10)
                
                current_time = timezone.now()
                update_info = service.get_real_time_updates()
                
                if update_info['has_updates']:
                    # Send update notification
                    event_data = {
                        'type': 'dashboard_update',
                        'timestamp': current_time.isoformat(),
                        'message': 'Dashboard data updated'
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                
                # Send heartbeat every minute
                if (current_time - last_check).seconds >= 60:
                    heartbeat_data = {
                        'type': 'heartbeat',
                        'timestamp': current_time.isoformat()
                    }
                    yield f"data: {json.dumps(heartbeat_data)}\n\n"
                    last_check = current_time
                    
            except Exception as e:
                logger.error(f"Dashboard stream error: {str(e)}")
                error_data = {
                    'type': 'error',
                    'message': 'Stream error occurred'
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-source'
    )
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Headers'] = 'Cache-Control'
    
    return response

@never_cache
@login_required
@require_http_methods(["POST"])
def force_dashboard_refresh(request):
    """Force refresh dashboard cache"""
    try:
        DashboardUpdateService.invalidate_cache()
        
        # Get fresh data
        service = CachedUnifiedDashboardService()
        dashboard_data = service.get_complete_dashboard_data()
        
        return JsonResponse({
            'success': True,
            'message': 'Dashboard refreshed successfully',
            'data': dashboard_data,
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Force refresh error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to refresh dashboard'
        }, status=500)

@never_cache
@login_required
@require_http_methods(["GET"])
def dashboard_health_check(request):
    """Health check for dashboard services"""
    try:
        # Check cache connectivity
        cache_status = 'ok'
        try:
            cache.set('health_check', 'test', 10)
            cache.get('health_check')
        except Exception:
            cache_status = 'error'
        
        # Check database connectivity
        db_status = 'ok'
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            db_status = 'error'
        
        # Check service status
        service_status = 'ok'
        try:
            service = CachedUnifiedDashboardService()
            service.get_real_time_updates()
        except Exception:
            service_status = 'error'
        
        overall_status = 'ok' if all(s == 'ok' for s in [cache_status, db_status, service_status]) else 'error'
        
        return JsonResponse({
            'success': True,
            'status': overall_status,
            'components': {
                'cache': cache_status,
                'database': db_status,
                'service': service_status
            },
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JsonResponse({
            'success': False,
            'status': 'error',
            'error': str(e)
        }, status=500)