import os
from django.core.management.base import BaseCommand
from core.auto_admin import ensure_superuser_synced

class Command(BaseCommand):
    help = 'Creates or updates a superuser automatically from environment variables.'

    def handle(self, *args, **options):
        username = os.getenv('ADMIN_USERNAME', 'admin').strip()
        self.stdout.write(f'Synchronizing superuser credentials for user "{username}"...')
        ensure_superuser_synced()
        self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" synchronized successfully.'))
