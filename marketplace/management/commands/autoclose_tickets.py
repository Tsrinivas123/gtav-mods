from django.core.management.base import BaseCommand
from marketplace.views import close_inactive_tickets

class Command(BaseCommand):
    help = 'Automatically close tickets resolved for more than 30 days without customer replies'

    def handle(self, *args, **options):
        self.stdout.write("Running auto-close script for resolved support tickets...")
        close_inactive_tickets()
        self.stdout.write(self.style.SUCCESS("Successfully processed auto-close!"))
