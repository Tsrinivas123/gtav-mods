import os
from django.core.files.storage import Storage, FileSystemStorage
from django.core.files.base import ContentFile
from django.conf import settings
from core import supabase_storage


class SupabaseStorage(Storage):
    """
    Custom Django Storage backend that connects to Supabase Storage (private bucket)
    with seamless local FileSystemStorage fallback when Supabase credentials are not set.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.local_storage = FileSystemStorage()

    def _save(self, name, content):
        # Normalize path
        normalized_name = name.replace('\\', '/').lstrip('/')

        # 1. If Supabase Storage is configured, upload to private bucket
        if supabase_storage.is_configured():
            content.seek(0)
            data = content.read()
            supabase_storage.upload_file(data, normalized_name)
            # Also keep local copy if local MEDIA_ROOT exists for zero-latency local caching
            try:
                if not self.local_storage.exists(normalized_name):
                    self.local_storage.save(normalized_name, ContentFile(data))
            except Exception:
                pass
            return normalized_name

        # 2. Local fallback when Supabase is not configured
        return self.local_storage.save(name, content)

    def _open(self, name, mode='rb'):
        normalized_name = name.replace('\\', '/').lstrip('/')

        # Check local disk first
        if self.local_storage.exists(normalized_name):
            return self.local_storage._open(normalized_name, mode)

        # Fetch from Supabase Storage if configured
        if supabase_storage.is_configured():
            raw_bytes = supabase_storage.download_file_bytes(normalized_name)
            if raw_bytes is not None:
                # Optionally cache to local disk
                try:
                    self.local_storage.save(normalized_name, ContentFile(raw_bytes))
                except Exception:
                    pass
                return ContentFile(raw_bytes, name=normalized_name)

        return self.local_storage._open(name, mode)

    def delete(self, name):
        normalized_name = name.replace('\\', '/').lstrip('/')

        # Never delete placeholder files
        if 'placeholder' in normalized_name.lower():
            return

        if supabase_storage.is_configured():
            supabase_storage.delete_file(normalized_name)

        if self.local_storage.exists(normalized_name):
            try:
                self.local_storage.delete(normalized_name)
            except Exception:
                pass

    def exists(self, name):
        normalized_name = name.replace('\\', '/').lstrip('/')
        if self.local_storage.exists(normalized_name):
            return True
        if supabase_storage.is_configured():
            return supabase_storage.file_exists(normalized_name)
        return False

    def url(self, name):
        normalized_name = name.replace('\\', '/').lstrip('/')
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        return f"{media_url.rstrip('/')}/{normalized_name}"
