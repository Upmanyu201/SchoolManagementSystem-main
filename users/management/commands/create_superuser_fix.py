from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Create SuperUser account after restore'

    def handle(self, *args, **options):
        username = 'SuperUser'
        password = 'Pyare@0987'
        
        # Delete existing user if exists
        if User.objects.filter(username=username).exists():
            User.objects.filter(username=username).delete()
            self.stdout.write(f'Deleted existing user: {username}')
        
        # Create new superuser
        user = User.objects.create_superuser(
            username=username,
            password=password,
            email='superuser@school.com'
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created superuser: {username}')
        )