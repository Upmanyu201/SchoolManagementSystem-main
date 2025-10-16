"""
WhatsApp Business API Webhook handler
"""

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json
import hashlib
import hmac

@csrf_exempt
@require_http_methods(["GET", "POST"])
def whatsapp_webhook(request):
    """Handle WhatsApp webhook verification and message status updates"""
    
    if request.method == "GET":
        # Webhook verification
        verify_token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        
        expected_token = getattr(settings, 'WHATSAPP_WEBHOOK_VERIFY_TOKEN', '')
        
        if verify_token == expected_token:
            return HttpResponse(challenge)
        else:
            return HttpResponse('Verification failed', status=403)
    
    elif request.method == "POST":
        # Handle incoming webhook data
        try:
            # Verify signature if app secret is configured
            app_secret = getattr(settings, 'WHATSAPP_APP_SECRET', '')
            if app_secret:
                signature = request.headers.get('X-Hub-Signature-256', '')
                if not verify_signature(request.body, signature, app_secret):
                    return HttpResponse('Invalid signature', status=403)
            
            # Parse webhook data
            data = json.loads(request.body)
            
            # Process webhook data
            process_webhook_data(data)
            
            return JsonResponse({'status': 'success'})
            
        except json.JSONDecodeError:
            return HttpResponse('Invalid JSON', status=400)
        except Exception as e:
            return HttpResponse(f'Error: {str(e)}', status=500)

def verify_signature(payload, signature, app_secret):
    """Verify webhook signature"""
    if not signature.startswith('sha256='):
        return False
    
    expected_signature = hmac.new(
        app_secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature[7:], expected_signature)

def process_webhook_data(data):
    """Process incoming webhook data"""
    # Handle message status updates, delivery receipts, etc.
    # This is where you can update message status in your database
    
    entries = data.get('entry', [])
    for entry in entries:
        changes = entry.get('changes', [])
        for change in changes:
            if change.get('field') == 'messages':
                value = change.get('value', {})
                
                # Handle message status updates
                statuses = value.get('statuses', [])
                for status in statuses:
                    message_id = status.get('id')
                    status_type = status.get('status')  # sent, delivered, read, failed
                    
                    # Update message status in database
                    update_message_status(message_id, status_type)
                
                # Handle incoming messages (if needed)
                messages = value.get('messages', [])
                for message in messages:
                    # Handle incoming message
                    handle_incoming_message(message)

def update_message_status(message_id, status):
    """Update message status in database"""
    # Import here to avoid circular imports
    from .models import MessageRecipient
    
    try:
        # Find message recipient by external message ID
        # You might need to add a field to store the WhatsApp message ID
        pass
    except:
        pass

def handle_incoming_message(message):
    """Handle incoming WhatsApp message"""
    # This is where you can handle replies, auto-responses, etc.
    pass