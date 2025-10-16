from django.core.management.base import BaseCommand
from messaging.services import MessagingService
from messaging.models import MessageLog
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Test messaging system with specific phone numbers'

    def add_arguments(self, parser):
        parser.add_argument('--numbers', nargs='+', default=['9955590919', '8210434250'],
                          help='Phone numbers to test')

    def handle(self, *args, **options):
        self.stdout.write("🧪 TESTING MESSAGING SYSTEM")
        self.stdout.write("=" * 50)
        
        # Test phone numbers
        test_numbers = [
            {'phone': num, 'name': f'Test User {i+1}'} 
            for i, num in enumerate(options['numbers'])
        ]
        
        # Test message
        test_message = f"🎓 School Management System Test\n\nSent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nMessaging system test successful!\n\n- School Admin"
        
        # Get admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_user(
                username='admin_test',
                email='admin@school.com',
                is_staff=True
            )
        
        # Initialize messaging service
        messaging_service = MessagingService()
        
        self.stdout.write(f"\n📱 Testing {len(test_numbers)} numbers...")
        
        for number_data in test_numbers:
            phone = number_data['phone']
            name = number_data['name']
            
            self.stdout.write(f"\n📞 Testing {name} ({phone})...")
            
            # Create message log
            message_log = MessageLog.objects.create(
                sender=admin_user,
                message_type='custom',
                recipient_type='INDIVIDUAL',
                message_content=test_message,
                total_recipients=1
            )
            
            # Test SMS
            try:
                sms_result = messaging_service.send_sms(phone, test_message)
                if sms_result['success']:
                    self.stdout.write(self.style.SUCCESS(f"✅ SMS sent successfully"))
                    message_log.successful_sends += 1
                else:
                    self.stdout.write(self.style.ERROR(f"❌ SMS failed: {sms_result.get('error')}"))
                    message_log.failed_sends += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ SMS error: {e}"))
                message_log.failed_sends += 1
            
            # Test WhatsApp
            try:
                whatsapp_result = messaging_service.send_whatsapp_cloud_api(phone, test_message)
                if whatsapp_result['success']:
                    self.stdout.write(self.style.SUCCESS(f"✅ WhatsApp sent successfully"))
                    message_log.successful_sends += 1
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ WhatsApp API failed: {whatsapp_result.get('error')}"))
                    
                    # Generate WhatsApp Web URL as fallback
                    web_url = messaging_service.send_whatsapp_web(phone, test_message)
                    self.stdout.write(f"🌐 WhatsApp Web URL: {web_url}")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ WhatsApp error: {e}"))
            
            message_log.status = 'SENT' if message_log.successful_sends > 0 else 'FAILED'
            message_log.save()
        
        self.stdout.write(self.style.SUCCESS("\n✨ Messaging test completed!"))