"""
WhatsApp API Views - Production Ready
Direct integration with Meta WhatsApp Cloud API
"""

import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from .services import MessagingService
from .models import MessageLog, MessageRecipient

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def send_whatsapp_api(request):
    """
    Direct WhatsApp API endpoint
    POST /messaging/api/send-whatsapp/
    """
    try:
        data = json.loads(request.body)
        to_number = data.get('to', '').strip()
        message = data.get('message', '').strip()
        
        # Validation
        if not to_number or not message:
            return JsonResponse({
                'success': False,
                'error': 'Both recipient number and message are required'
            }, status=400)
        
        # Validate phone number format
        clean_number = ''.join(filter(str.isdigit, to_number))
        if len(clean_number) not in [10, 12]:  # 10 for local, 12 for international
            return JsonResponse({
                'success': False,
                'error': 'Invalid phone number format'
            }, status=400)
        
        # Send message
        service = MessagingService()
        result = service.send_whatsapp_cloud_api(to_number, message)
        
        # Log the attempt
        message_log = MessageLog.objects.create(
            sender=request.user,
            message_type='WHATSAPP',
            recipient_type='INDIVIDUAL',
            message_content=message,
            total_recipients=1,
            successful_sends=1 if result['success'] else 0,
            failed_sends=0 if result['success'] else 1,
            status='SENT' if result['success'] else 'FAILED'
        )
        
        MessageRecipient.objects.create(
            message_log=message_log,
            phone_number=to_number,
            name=data.get('name', 'Unknown'),
            role='API_USER',
            status='SENT' if result['success'] else 'FAILED',
            error_message=result.get('error', '')
        )
        
        if result['success']:
            logger.info(f"WhatsApp API success: {request.user.username} -> {to_number}")
            return JsonResponse({
                'success': True,
                'message_id': result.get('message_id'),
                'to': result.get('to'),
                'log_id': message_log.id
            })
        else:
            logger.warning(f"WhatsApp API failed: {request.user.username} -> {to_number}: {result.get('error')}")
            return JsonResponse({
                'success': False,
                'error': result.get('error'),
                'log_id': message_log.id
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"WhatsApp API error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def bulk_whatsapp_api(request):
    """
    Bulk WhatsApp API endpoint
    POST /messaging/api/bulk-whatsapp/
    """
    try:
        data = json.loads(request.body)
        recipients = data.get('recipients', [])
        message = data.get('message', '').strip()
        
        if not recipients or not message:
            return JsonResponse({
                'success': False,
                'error': 'Recipients list and message are required'
            }, status=400)
        
        if len(recipients) > 100:  # Rate limiting
            return JsonResponse({
                'success': False,
                'error': 'Maximum 100 recipients per bulk send'
            }, status=400)
        
        # Create message log
        message_log = MessageLog.objects.create(
            sender=request.user,
            message_type='WHATSAPP',
            recipient_type='BULK',
            message_content=message,
            total_recipients=len(recipients),
            successful_sends=0,
            failed_sends=0,
            status='PROCESSING'
        )
        
        # Process recipients
        service = MessagingService()
        processed_recipients = []
        
        for recipient in recipients:
            phone = recipient.get('phone', '').strip()
            name = recipient.get('name', 'Unknown')
            
            if not phone:
                continue
                
            processed_recipients.append({
                'phone': phone,
                'name': name,
                'role': 'BULK_USER'
            })
        
        # Send bulk messages
        results = service.send_bulk_whatsapp_cloud_api(processed_recipients, message, message_log)
        
        logger.info(f"Bulk WhatsApp completed: {request.user.username} sent to {len(processed_recipients)} recipients")
        
        return JsonResponse({
            'success': True,
            'log_id': message_log.id,
            'total_recipients': len(processed_recipients),
            'successful_sends': message_log.successful_sends,
            'failed_sends': message_log.failed_sends,
            'results': len(results)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        logger.error(f"Bulk WhatsApp API error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

@require_http_methods(["GET"])
@login_required
def whatsapp_status(request):
    """
    WhatsApp service status endpoint
    GET /messaging/api/status/
    """
    try:
        service = MessagingService()
        
        # Test token validity
        phone_id = service.get_whatsapp_phone_id()
        
        status = {
            'whatsapp_configured': bool(service.whatsapp_token),
            'phone_id_available': bool(phone_id),
            'phone_id': phone_id,
            'api_version': service.whatsapp_version,
            'business_id': service.whatsapp_business_id
        }
        
        return JsonResponse({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"WhatsApp status check error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)