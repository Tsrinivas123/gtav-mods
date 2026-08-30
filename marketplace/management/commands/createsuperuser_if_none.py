import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Creates or updates a superuser automatically from environment variables.'

    def handle(self, *args, **options):
        username = os.getenv('ADMIN_USERNAME', 'admin')
        email = os.getenv('ADMIN_EMAIL', 'admin@pawanmod.com')
        password = os.getenv('ADMIN_PASSWORD', 'admin123')

        superuser = User.objects.filter(is_superuser=True).first() or User.objects.filter(username=username).first()

        if superuser:
            self.stdout.write(f'Updating superuser credentials for user "{username}"...')
            superuser.username = username
            superuser.email = email
            superuser.set_password(password)
            superuser.is_superuser = True
            superuser.is_staff = True
            superuser.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" updated successfully.'))
        else:
            self.stdout.write(f'Creating superuser "{username}"...')
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully.'))
