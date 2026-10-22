import os
from django.core.files.storage import Storage, FileSystemStorage
from django.core.files.base import ContentFile
from django.conf import settings
from core import supabase_storage


class SupabaseStorage(Storage):
    """
    Custom Django Storage backend that connects to Supabase Storage (private bucket)
    with seamless local FileSystemStorage fallback when Supabase credentials are not set.
    Ensures production uploads never attempt to write to read-only local filesystems (e.g. Vercel).
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.local_storage = FileSystemStorage()

    @property
    def _is_vercel(self):
        return getattr(settings, 'IS_VERCEL', False) or os.getenv('VERCEL') == '1' or 'VERCEL' in os.environ

    def _save(self, name, content):
        # Normalize path
        normalized_name = name.replace('\\', '/').lstrip('/')

        # 1. If Supabase Storage is configured, upload to private bucket directly
        if supabase_storage.is_configured():
            content.seek(0)
            data = content.read()
            supabase_storage.upload_file(data, normalized_name)
            return normalized_name

        # 2. Local fallback when Supabase is not configured
        if self._is_vercel:
            raise RuntimeError(
                "Supabase Storage is not configured on Vercel. Remote storage must be configured "
                "with SUPABASE_URL and SUPABASE_SERVICE_KEY because the local filesystem is read-only."
            )
        return self.local_storage.save(name, content)

    def _open(self, name, mode='rb'):
        normalized_name = name.replace('\\', '/').lstrip('/')

        # Check local disk first (for local development outside Vercel)
        if not self._is_vercel:
            try:
                if self.local_storage.exists(normalized_name):
                    return self.local_storage._open(normalized_name, mode)
            except Exception:
                pass

        # Fetch from Supabase Storage if configured
        if supabase_storage.is_configured():
            raw_bytes = supabase_storage.download_file_bytes(normalized_name)
            if raw_bytes is not None:
                return ContentFile(raw_bytes, name=normalized_name)

        if not self._is_vercel:
            return self.local_storage._open(name, mode)
        raise FileNotFoundError(f"File '{normalized_name}' not found in remote storage.")

    def delete(self, name):
        normalized_name = name.replace('\\', '/').lstrip('/')

        # Never delete placeholder files
        if 'placeholder' in normalized_name.lower():
            return

        if supabase_storage.is_configured():
            supabase_storage.delete_file(normalized_name)

        if not self._is_vercel:
            try:
                if self.local_storage.exists(normalized_name):
                    self.local_storage.delete(normalized_name)
            except Exception:
                pass

    def exists(self, name):
        normalized_name = name.replace('\\', '/').lstrip('/')
        if not self._is_vercel:
            try:
                if self.local_storage.exists(normalized_name):
                    return True
            except Exception:
                pass
        if supabase_storage.is_configured():
            return supabase_storage.file_exists(normalized_name)
        return False

    def url(self, name):
        normalized_name = name.replace('\\', '/').lstrip('/')
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        return f"{media_url.rstrip('/')}/{normalized_name}"
