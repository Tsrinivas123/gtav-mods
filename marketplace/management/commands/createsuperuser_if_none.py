import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Creates a superuser automatically from environment variables if no superuser exists.'

    def handle(self, *args, **options):
        username = os.getenv('ADMIN_USERNAME', 'admin')
        email = os.getenv('ADMIN_EMAIL', 'admin@pawanmod.com')
        password = os.getenv('ADMIN_PASSWORD', 'admin123')

        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write(f'No superuser found. Creating admin user "{username}"...')
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully.'))
        else:
            self.stdout.write(self.style.SUCCESS('Superuser already exists. Skipping creation.'))
