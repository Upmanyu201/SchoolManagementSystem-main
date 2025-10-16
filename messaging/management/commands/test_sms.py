from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from messaging.services import MSG91Service

User = get_user_model()

class Command(BaseCommand):
    help = 'Test MSG91 SMS'
    
    def add_arguments(self, parser):
        parser.add_argument('--phone', required=True, help='Phone number')
        parser.add_argument('--message', default='Test SMS from School', help='Message')
    
    def handle(self, *args, **options):
        phone = options['phone']
        message = options['message']
        
        service = MSG91Service()
        result = service.send_sms(phone, message)
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f'SMS sent! ID: {result["message_id"]}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'SMS failed: {result["error"]}')
            )