from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import uuid

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def export_initiate(request):
    """Export API endpoint for attendance and other modules"""
    try:
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body) if request.body else {}
        else:
            data = dict(request.POST)
            # Convert single-item lists to strings
            for key, value in data.items():
                if isinstance(value, list) and len(value) == 1:
                    data[key] = value[0]
        
        module = data.get('module', 'unknown')
        format_type = data.get('format', 'csv')
        
        logger.info(f"Export request - Module: {module}, Format: {format_type}")
        
        # Generate a mock request ID for now
        import uuid
        request_id = str(uuid.uuid4())[:8]
        
        return JsonResponse({
            'success': True,
            'request_id': request_id,
            'message': f'{format_type.upper()} export initiated successfully',
            'module': module,
            'format': format_type
        })
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Export request failed',
            'message': 'Please try again later'
        }, status=500)


@require_http_methods(["GET"])
def export_status(request, request_id):
    """Check export status"""
    try:
        # For now, simulate completed status after a short delay
        return JsonResponse({
            'status': 'completed',
            'request_id': request_id,
            'message': 'Export completed successfully'
        })
    except Exception as e:
        logger.error(f"Export status error: {str(e)}")
        return JsonResponse({
            'status': 'failed',
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def export_download(request, request_id):
    """Download export file"""
    try:
        from django.http import HttpResponse
        
        # Create a simple CSV response for now
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="export_{request_id}.csv"'
        
        # Simple CSV content
        response.write('Name,Status,Date\n')
        response.write('Sample Export,Completed,2025-01-27\n')
        
        return response
    except Exception as e:
        logger.error(f"Export download error: {str(e)}")
        return JsonResponse({
            'error': 'Download failed',
            'message': str(e)
        }, status=500)