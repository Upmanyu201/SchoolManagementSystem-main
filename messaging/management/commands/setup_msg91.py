from django.core.management.base import BaseCommand
from messaging.models import MSG91Config

class Command(BaseCommand):
    help = 'Setup MSG91 configuration'
    
    def handle(self, *args, **options):
        config, created = MSG91Config.objects.get_or_create(
            is_active=True,
            defaults={
                'auth_key': '466878AbS44RRkI68b3cabfP1',
                'sender_id': 'TXTLCL'
            }
        )
        
        if not created:
            config.auth_key = '466878AbS44RRkI68b3cabfP1'
            config.sender_id = 'TXTLCL'
            config.save()
        
        self.stdout.write(
            self.style.SUCCESS('MSG91 configured successfully!')
        )