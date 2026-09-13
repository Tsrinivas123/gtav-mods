import os
from django.core.management.base import BaseCommand
from django.conf import settings
from core import supabase_storage


class Command(BaseCommand):
    help = 'Safely migrates local media files to the private Supabase Storage bucket without deleting local files.'

    def handle(self, *args, **options):
        if not supabase_storage.is_configured():
            self.stdout.write(self.style.ERROR(
                'Supabase Storage is not configured. Please set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables.'
            ))
            return

        media_root = settings.MEDIA_ROOT
        if not os.path.exists(media_root):
            self.stdout.write(self.style.WARNING(f'MEDIA_ROOT directory "{media_root}" does not exist.'))
            return

        self.stdout.write(self.style.NOTICE(f'Scanning "{media_root}" for media files to migrate to Supabase Storage...'))

        uploaded_count = 0
        skipped_count = 0
        error_count = 0

        for root, _, files in os.walk(media_root):
            for file_name in files:
                local_file_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(local_file_path, media_root).replace('\\', '/')

                try:
                    # Check if file exists in Supabase
                    if supabase_storage.file_exists(rel_path):
                        self.stdout.write(f'  [SKIPPED - EXISTS] {rel_path}')
                        skipped_count += 1
                        continue

                    # Read and upload file
                    with open(local_file_path, 'rb') as f:
                        supabase_storage.upload_file(f, rel_path)

                    self.stdout.write(self.style.SUCCESS(f'  [UPLOADED] {rel_path}'))
                    uploaded_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  [ERROR] {rel_path}: {e}'))
                    error_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nMigration complete: {uploaded_count} uploaded, {skipped_count} skipped, {error_count} errors.\n'
            f'Local media files have been preserved untouched.'
        ))
